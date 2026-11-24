import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace as NS

import pytest

from app.config import default_settings
from app.gemini_client import (
    Citation,
    GeminiError,
    GeminiService,
    build_request,
    friendly_error,
    iter_pieces,
)

PNG = b"\x89PNG\r\n\x1a\nfake"


def test_build_request_default_preset():
    s = default_settings()
    req = build_request(s.active_preset(), s, PNG)
    assert req["model"] == "gemini-4-hydrogen"
    assert req["store"] is False and req["stream"] is True
    image, text = req["input"]
    assert image == {"type": "image", "data": base64.b64encode(PNG).decode(),
                     "mime_type": "image/jpeg", "resolution": "high"}
    assert text["type"] == "text" and text["text"]
    assert "español" in req["system_instruction"]
    assert req["generation_config"] == {"thinking_level": "low"}
    assert "tools" not in req


def test_build_request_search_tokens_and_model_default_thinking():
    s = default_settings()
    p = next(p for p in s.presets if p.id == "definicion")
    p.thinking_level = ""
    p.max_output_tokens = 800
    p.model = "gemini-3.5-flash-lite"
    p.resolution = "ultra_high"
    req = build_request(p, s, PNG)
    assert req["model"] == "gemini-3.5-flash-lite"
    assert req["tools"] == [{"type": "google_search"}]
    assert req["generation_config"] == {"max_output_tokens": 800}  # sin thinking_level
    assert req["input"][0]["resolution"] == "ultra_high"


def test_build_request_coerces_invalid_level_and_omits_empty_fields():
    s = default_settings()
    p = s.active_preset()
    p.thinking_level = "minimal"  # Gemini 4 no lo admite
    p.system_instruction = "   "
    p.prompt = ""
    req = build_request(p, s, PNG)
    assert req["generation_config"]["thinking_level"] == "low"
    assert "system_instruction" not in req
    assert req["input"][1]["text"] == "Analiza la captura."


def test_request_validates_against_sdk_schema():
    from google.genai._gaos.types.interactions import CreateModelInteraction

    s = default_settings()
    p = next(p for p in s.presets if p.id == "definicion")
    req = build_request(p, s, PNG)
    req.pop("stream")
    model = CreateModelInteraction.model_validate(req)
    assert model.store is False


def test_iter_pieces_text_citations_and_error():
    events = [
        NS(event_type="interaction.created"),
        NS(event_type="step.start", step=NS(type="google_search_call")),
        NS(event_type="step.delta", delta=NS(type="thought_summary", text="pensando")),
        NS(event_type="step.delta", delta=NS(type="text", text="Hola ")),
        NS(event_type="step.delta", delta=NS(type="text", text="mundo")),
        NS(event_type="step.delta", delta=NS(type="text_annotation_delta", annotations=[
            NS(type="url_citation", url="https://www.boe.es/x", title="boe.es")])),
        NS(event_type="interaction.completed"),
    ]
    pieces = list(iter_pieces(events))
    assert "".join(p.text for p in pieces) == "Hola mundo"
    assert pieces[-1].citations == [Citation("https://www.boe.es/x", "boe.es")]

    with pytest.raises(GeminiError, match="cuota"):
        list(iter_pieces([NS(event_type="error", error=NS(code="429", message="cuota"))]))


def test_friendly_errors():
    assert "API key" in friendly_error(_E(401))
    assert "429" in friendly_error(_E(429))
    assert "404" in friendly_error(_E(404))
    assert "timeout" in friendly_error(type("APITimeoutError", (Exception,), {})("t"))


class _E(Exception):
    def __init__(self, code):
        super().__init__(f"error {code}")
        self.status_code = code


# --------------------------------------------------------------------------- SDK real + servidor falso


class _FakeGemini(BaseHTTPRequestHandler):
    received: list = []

    def log_message(self, *args):
        pass

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _FakeGemini.received.append((self.path, body))
        events = [
            {"event_type": "interaction.created", "interaction": {"id": "i1", "status": "in_progress"}},
            {"event_type": "step.delta", "index": 0, "delta": {"type": "text", "text": "**Base "}},
            {"event_type": "step.delta", "index": 0, "delta": {"type": "text", "text": "reguladora**"}},
            {"event_type": "interaction.completed", "interaction": {"id": "i1", "status": "completed"}},
        ]
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for ev in events:
            self.wfile.write(f"event: {ev['event_type']}\ndata: {json.dumps(ev)}\n\n".encode())
        self.wfile.write(b"data: [DONE]\n\n")


def test_stream_through_real_sdk(monkeypatch):
    for var in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
        monkeypatch.delenv(var, raising=False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeGemini)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        from google import genai

        svc = GeminiService(lambda key: genai.Client(api_key=key, http_options={"base_url": base}))
        s = default_settings()
        req = build_request(s.active_preset(), s, PNG)
        text = "".join(p.text for p in svc.stream("clave-falsa", req))
    finally:
        server.shutdown()

    assert text == "**Base reguladora**"
    path, body = _FakeGemini.received[-1]
    assert path.endswith("/interactions")
    assert body["model"] == "gemini-4-hydrogen"
    assert body["store"] is False and body["stream"] is True
    # El SDK envuelve imagen + texto en un paso "user_input".
    step = body["input"][0]
    assert step["type"] == "user_input"
    image, text = step["content"]
    assert image["type"] == "image" and image["resolution"] == "high" and image["mime_type"] == "image/jpeg"
    assert base64.b64decode(image["data"]) == PNG
    assert text["type"] == "text" and text["text"]
    assert body["system_instruction"].startswith("Eres un tutor")
    assert body["generation_config"] == {"thinking_level": "low"}


def test_service_start_reports_errors_via_callback():
    class Boom:
        class interactions:  # noqa: N801
            @staticmethod
            def create(**kw):
                raise _E(429)

    svc = GeminiService(lambda key: Boom())
    done, errors = threading.Event(), []
    t = svc.start("k", {"model": "m"}, on_piece=lambda p: None, on_done=done.set,
                  on_error=lambda m: (errors.append(m), done.set()))
    t.join(5)
    assert errors and "429" in errors[0]
