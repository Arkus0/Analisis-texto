from app.models import coerce_thinking_level, is_chat_model, normalize_model_id, thinking_levels


def test_levels_per_model():
    assert thinking_levels("gemini-4-hydrogen") == (["low", "medium", "high", "xhigh"], "high")
    assert thinking_levels("gemini-3.5-flash-lite") == (["minimal", "low", "medium", "high"], "minimal")
    assert thinking_levels("models/gemini-4-carbon")[1] == "medium"


def test_unknown_model_falls_back():
    assert thinking_levels("gemini-9-ultra") == (["low", "medium", "high"], None)


def test_coerce_keeps_valid_and_maps_invalid_to_nearest():
    assert coerce_thinking_level("gemini-4-hydrogen", "low") == "low"
    assert coerce_thinking_level("gemini-4-hydrogen", "minimal") == "low"  # Gemini 4 no tiene minimal
    assert coerce_thinking_level("gemini-4-carbon", "xhigh") == "high"
    assert coerce_thinking_level("gemini-3.5-flash-lite", "minimal") == "minimal"
    assert coerce_thinking_level("gemini-4-hydrogen", "") == ""
    assert coerce_thinking_level("gemini-4-hydrogen", "rarísimo") == ""


def test_chat_model_filter():
    assert is_chat_model("models/gemini-4-hydrogen")
    assert is_chat_model("gemini-3.5-flash-lite")
    assert not is_chat_model("gemini-3.8-flash-tts")
    assert not is_chat_model("gemini-3.1-flash-image")
    assert not is_chat_model("gemini-embedding-002")
    assert not is_chat_model("lyria-3.5")
    assert normalize_model_id(" models/gemini-x ") == "gemini-x"
