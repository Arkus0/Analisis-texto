# Overlay Gemini

Pregunta a Gemini por lo que tienes en pantalla **mientras OBS sigue grabando**, sin
pausar, minimizar ni cambiar de ventana.

- **Un solo botón** del mando (8BitDo, Switch Pro, DualShock/DualSense, Xbox…), del
  ratón (laterales X1/X2 o central) o del teclado.
- **Pulsación corta** con la franja oculta → captura la pantalla, la envía a Gemini con
  tu prompt y muestra la respuesta en una **franja central** que se ajusta sola al texto.
- **Pulsación corta** con la franja visible → la oculta.
- **Pulsación larga** (0,6 s) → vuelve a mostrar la última respuesta, sin nueva captura.
- La franja es **invisible para OBS** y para cualquier grabación o captura. No roba el
  foco y deja pasar los clics.

## Instalación

### Opción A · `.exe` ya compilado (sin instalar Python)
1. En GitHub, abre **Actions → "overlay-gemini (Windows .exe)"**, entra en la última
   ejecución correcta y descarga el artefacto **OverlayGemini-windows**.
2. Descomprímelo donde quieras y ejecuta `OverlayGemini.exe`.

### Opción B · Desde el código
Requiere Windows 10 2004+ (o Windows 11) y Python 3.11+.
```bat
cd overlay_gemini
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Para generar tu propio `.exe`, ejecuta `build.bat`. Hace los tests y la compilación y
deja el resultado en `dist\OverlayGemini\`.

## Primer uso
La primera vez se abre **Ajustes**. Después lo encuentras en el icono de la bandeja del
sistema (clic o menú → *Ajustes…*).
1. **API key**: créala gratis en <https://aistudio.google.com/apikey> y pégala. Se
   guarda en el Administrador de credenciales de Windows, no en un archivo de texto. Si
   ya tienes la variable de entorno `GEMINI_API_KEY`, se usa esa.
2. **Botón**: pulsa *Asignar…* y después el botón que quieras usar.
3. **Prompt activo**: elige *Dudas*, *Definición exacta*, *Traducción* o uno tuyo.
4. **Guardar y probar**: hace una captura de prueba en ese momento.

## Mientras grabas
| Acción | Resultado |
|---|---|
| Pulsación corta (franja oculta) | Captura → "Analizando…" → la respuesta aparece en streaming |
| Pulsación corta (franja visible) | Oculta la franja |
| Pulsación larga | Vuelve a mostrar la última respuesta (o el último error) |

Si ocultas la franja antes de que termine la respuesta, esta sigue llegando en segundo
plano. Una pulsación larga te la enseña.

**Comprobar que no se graba:** con la franja visible, mira la vista previa de OBS; no
debe aparecer. Funciona con *Captura de pantalla* y con *Captura de ventana*.

## Prompts y modelos (noviembre 2026)
Cada prompt tiene su *system instruction*, su texto y, opcionalmente:
- **Modelo propio**: si lo dejas vacío, usa el modelo global.
- **Razonamiento** (`thinking_level`): solo se ofrecen los niveles válidos para el
  modelo. "Por defecto del modelo" no envía nada. Gemini 4 no tiene "mínimo"; Flash-Lite sí.
- **Resolución de imagen**: *Alta* (1120 tokens) es la recomendada; *Ultra* sirve para
  letra muy pequeña.
- **Buscar en Google**: contrasta la respuesta con la web y muestra las fuentes. Incluye
  5.000 búsquedas al mes gratis; a partir de ahí cuesta 14 $ por cada 1.000.
- **Máx. tokens**: normalmente "Sin límite". La brevedad la marca el system instruction.

| Modelo | Para qué |
|---|---|
| `gemini-4-hydrogen` *(por defecto)* | General, rápido y fiable · capa gratuita |
| `gemini-3.5-flash-lite` | El más rápido y barato · capa gratuita |
| `gemini-3.8-flash` / `gemini-3.6-flash` | Flash · capa gratuita |
| `gemini-4-carbon` / `-neon` / `-argon` | Máxima calidad · solo de pago |

El botón **Cargar modelos de la API** añade a la lista todos los modelos que tu clave
puede usar. Así no se queda anticuada.

### Privacidad
- Cada captura se envía con `store=False`: Google no guarda la interacción para
  recuperarla después. La app tampoco guarda nada en disco, salvo los ajustes.
- Con una clave de la **capa gratuita**, Google puede usar el contenido para mejorar sus
  productos. Si las capturas son sensibles, usa una clave con facturación activada.

## La franja
Se adapta a cada respuesta y **nunca hay que hacer scroll**:
1. El ancho es el que necesita el texto, hasta el 70 % del monitor.
2. El alto crece desde el centro, hasta el 45 % del monitor.
3. Si no cabe, se ensancha al 95 % y después reduce la letra hasta el 70 %.
4. Si aun así no cabe, lo que sería muy raro con los prompts por defecto, se recorta
   con un aviso.

Todo esto (posición, anchos, alto, opacidad y letra) se ajusta en *Ajustes → Franja*,
que tiene vista previa.

## Mandos y botones
- **Steam abierto**: Steam Input puede "secuestrar" el mando. Ciérralo o desactiva Steam
  Input para ese mando. En Ajustes → General → *Mandos* ves qué mandos detecta la app.
- **8BitDo**: funciona en modo X-input, D-input y Switch.
- **Ratón**: el botón asignado se bloquea para el resto de programas. X1 deja de hacer
  "Atrás" en el navegador mientras la app está abierta.
- **Teclado**: la tecla asignada también se bloquea. Mejor una que no uses: F13–F24,
  Pausa, Bloq Despl…

## Solución de problemas
| Problema | Solución |
|---|---|
| La franja sale en la grabación | Necesitas Windows 10 2004 o posterior. Ajustes avisa si Windows no lo permite. |
| No reacciona al mando | Mira *Mandos* en Ajustes. Cierra Steam y vuelve a asignar el botón. |
| "API key no válida" | Vuelve a copiarla de AI Studio. |
| "Cuota agotada (429)" | Espera un minuto o usa `gemini-3.5-flash-lite`. |
| La respuesta es demasiado larga | Endurece el system instruction (p. ej. "máximo 4 líneas"). |

## Desarrollo
```bash
pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen python -m pytest -q   # tests (también en Linux)
python main.py --selftest                       # comprueba dependencias
python build.py                                 # .exe con PyInstaller
```
Estructura:
- `app/controller.py`: lógica del botón.
- `app/overlay.py`: la franja y su ajuste.
- `app/gemini_client.py`: Interactions API.
- `app/input/`: mando (SDL2), ratón y teclado (pynput).
- `app/win32.py`: exclusión de captura y estilos de ventana.
- `app/settings_window.py`: la ventana de ajustes.
