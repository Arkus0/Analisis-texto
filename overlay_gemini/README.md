# Overlay Gemini

Pregunta a Gemini por lo que tienes en pantalla **mientras OBS graba**, sin tocar OBS,
sin pausas y sin avisos. Solo con el mando.

- **Pulsación corta** → captura la pantalla. Aparece un **icono pequeño** en el centro
  mientras Gemini piensa. Cuando la respuesta está completa, el icono se desvanece y
  entra la **franja** con un fundido suave.
- **Pulsación corta** con la franja visible → se desvanece.
- **Pulsación corta** con el icono girando → cancela la espera. Esa respuesta **no**
  aparecerá sola después.
- **Pulsación larga** (0,6 s) → vuelve a mostrar la última respuesta. Si aún no ha
  llegado, vuelve a mostrar el icono.
- **Si algo falla** (sin internet, cuota, más de 40 s): el icono se pone **rojo 2 s** y
  desaparece. Nada más. El detalle se ve con una pulsación larga.

## Convivencia con OBS
La app está hecha para que OBS no note nada:

| Garantía | Cómo |
|---|---|
| OBS no depende de la app | Es un programa aparte: no hay plugin ni websocket. Si la app se cerrara de golpe, OBS seguiría igual. |
| No toca la capturadora | Nunca abre la Cam Link ni ningún dispositivo de vídeo, porque solo un programa puede usarlos a la vez. |
| OBS siempre tiene preferencia | La app se ejecuta con prioridad *por debajo de lo normal*. |
| No usa la GPU | Dibuja en CPU. No compite con el codificador de OBS (NVENC/QSV/x264). |
| Casi nada en reposo | Con todo oculto no hay animaciones ni temporizadores; solo se lee el mando 100 veces por segundo. |
| Sin hooks con mando | Si el botón es del mando, la app **no** intercepta el ratón ni el teclado. |
| Animaciones baratas | Los fundidos solo cambian la opacidad. La franja se dibuja una única vez. |
| Captura ligera | Una sola copia de pantalla por pulsación, como un Impr Pant. El JPEG se prepara en segundo plano. |
| Invisible en la grabación | El icono y la franja no aparecen en ninguna captura (requiere Windows 10 2004+). |
| Cero avisos | Sin notificaciones, globos ni ventanas emergentes. Los errores van a un log. |

### Comprobar que OBS no lo nota (recomendado la primera vez)
1. En OBS: **Ver → Paneles → Estadísticas**.
2. Graba 5 min **sin** la app y apunta "Fotogramas perdidos por retraso de
   renderizado" y "Fotogramas omitidos por retraso de codificación".
3. Graba otros 5 min con la app y, desde el icono de la bandeja, lanza **"Prueba de
   impacto en OBS (3 min, sin gastar API)"**. Simula una pulsación cada 10 s:
   captura, icono, franja y ocultar.
4. Los dos contadores deben quedarse igual que sin la app.

## Montaje con capturadora (Cam Link) — recomendado
El curso llega a OBS por la capturadora. Para verlo bien y que Gemini reciba solo el curso:
1. En OBS, **clic derecho en la vista previa → Proyector a pantalla completa (vista
   previa) →** tu monitor.
2. Ves el curso a pantalla completa y nítido. OBS sigue grabando igual.
3. En la app: *Ajustes → Captura → Zona de captura* = **Pantalla completa**.

Para salir del proyector, pulsa Esc o haz clic derecho → *Cerrar*.

**Si prefieres ver OBS maximizado:** *Ajustes → Captura → Elegir zona…* y marca con el
ratón la vista previa de OBS. Así Gemini solo recibe esa parte, más grande y sin los
menús de OBS.

## Instalación
### Opción A · `.exe` ya compilado
1. En GitHub, abre **Actions → "overlay-gemini (Windows .exe)"**, entra en la última
   ejecución correcta y descarga **OverlayGemini-windows**.
2. Descomprímelo y abre `OverlayGemini.exe` **una vez antes de grabar**. Windows
   SmartScreen puede preguntar la primera vez: *Más información → Ejecutar de todas formas*.

### Opción B · Desde el código
Requiere Windows 10 2004+ (o 11) y Python 3.11+.
```bat
cd overlay_gemini
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
Para generar tu propio `.exe`, ejecuta `build.bat`.

## Primer uso (antes de grabar)
1. **API key**: créala en <https://aistudio.google.com/apikey> y pégala en Ajustes.
   Debajo verás "✔ Clave válida y conexión preparada".
2. **Botón**: *Asignar…* y pulsa el botón del mando.
3. **Prompt**: crea el tuyo para el curso en la pestaña *Prompts* y elígelo como
   *Prompt activo*.
4. **Velocidad**: en la pestaña *Velocidad*, *Capturar y comparar* envía una captura
   con tu prompt a varios modelos y te dice cuánto tarda cada uno y qué responde. Elige
   el modelo según eso.
5. Activa el **"No molestar"** de Windows (*Configuración → Sistema → Notificaciones*)
   para que **otros** programas tampoco muestren avisos mientras grabas.
6. Opcional: marca **"Arrancar con Windows"** en *Ajustes → General → Inicio* y no
   tendrás que acordarte de abrirla.

A partir de ahí: abres OBS, y solo el mando.

## Arrancar con Windows
Con la casilla *Ajustes → General → Inicio → "Arrancar con Windows"* la app se abre sola
al iniciar sesión, **directamente en la bandeja y sin ninguna ventana**, aunque falte
configurar algo. En ese caso Ajustes se abre desde el icono de la bandeja cuando quieras.

- Se guarda solo para tu usuario, en la lista de arranque de Windows. No necesita
  permisos de administrador.
- La verás en *Administrador de tareas → Aplicaciones de arranque* como "OverlayGemini",
  y también se puede desactivar desde ahí.
- Si mueves la carpeta del `.exe`, la app corrige la ruta sola la próxima vez que la abras.

## Velocidad
Lo que tarda la propia app es menos de 0,6 s por pulsación:
- captura ~50 ms;
- JPEG en segundo plano ~30 ms;
- subida de ~300 KB.

El resto depende del modelo, del razonamiento y de lo larga que sea la respuesta. Ten en
cuenta que la franja aparece **cuando la respuesta está completa**.

| Modelo | Orientativo | Para qué |
|---|---|---|
| `gemini-3.5-flash-lite` | ~1–3 s | El más rápido. Bueno para dudas y traducciones |
| `gemini-4-hydrogen` | ~3–7 s | Más fiable para definiciones exactas |
| + Buscar en Google | +1–3 s | Contrasta con la web y muestra las fuentes |

Son estimaciones: mídelo con **Ajustes → Velocidad**. Respuestas más cortas (pídelo en
el system instruction) = franja antes.

### Conexión siempre preparada (sin gastar tokens)
La app mantiene abierta la conexión con Gemini. Así, la primera pulsación tras un rato
sin usarla no tarda ~0,3 s de más en negociar la conexión segura.

- Si pasan 2,5 minutos sin tráfico, pide a Gemini los **datos del modelo**. Es una
  petición de 1–2 KB: **no genera texto y no gasta tokens**.
- De paso comprueba la clave. Si al arrancar Windows aún no había red, el estado en
  Ajustes ("✔ Clave válida…") se corrige solo.
- No hace nada si no hay API key ni durante la prueba de impacto.

## Prompts
Cada prompt tiene:
- *System instruction* y texto;
- **modelo** propio (opcional);
- **razonamiento**: solo se ofrecen los niveles válidos del modelo;
- **resolución de imagen**: *Alta* es la recomendada; *Ultra*, para letra pequeña;
- **búsqueda en Google** opcional;
- máximo de tokens.

Se usa siempre el *Prompt activo* elegido en Ajustes: durante la grabación no hay
selector.

### Privacidad
- Cada captura se envía con `store=False`: Google no la guarda para recuperarla después.
- La app no guarda capturas ni respuestas en disco. El log solo apunta tiempos y errores.
- Con una clave de la **capa gratuita**, Google puede usar el contenido para mejorar sus
  productos. Si los cursos son sensibles, usa una clave con facturación.

## La franja
Se ajusta sola a cada respuesta y **nunca hay que hacer scroll**:
1. Su ancho es el que necesita el texto (máximo 70 %).
2. Crece desde el centro (máximo 45 % de alto).
3. Si no cabe, se ensancha y después reduce un poco la letra.

Todo se ajusta en *Ajustes → Franja*, con vista previa: posición, tamaños, opacidad,
letra y duración del fundido.

## Mandos
- **Steam abierto**: Steam Input puede quedarse el mando. Ciérralo o desactiva Steam
  Input para ese mando. En *Ajustes → General → Mandos* ves qué detecta la app.
- 8BitDo (X-input, D-input o modo Switch), Switch Pro, DualShock/DualSense y Xbox
  funcionan en segundo plano.
- Si asignas un botón de **ratón o teclado**, ese botón se bloquea para los demás
  programas. Solo en ese caso la app intercepta el ratón o el teclado.

## Solución de problemas
| Problema | Solución |
|---|---|
| El icono se pone rojo | Pulsación larga para leer el error. También está en `%APPDATA%\OverlayGemini\overlay.log`. |
| La franja sale en la grabación | Necesitas Windows 10 2004 o posterior. Ajustes avisa si Windows no lo permite. |
| No reacciona al mando | Mira *Mandos* en Ajustes. Cierra Steam y vuelve a asignar el botón. |
| Tarda demasiado | Usa `gemini-3.5-flash-lite` o razonamiento "Mínimo". Pide respuestas más cortas o quita la búsqueda. |
| El icono no sale encima del proyector | Pulsa otra vez: la app se recoloca encima en cada aparición. Si OBS tiene "Proyectores siempre encima", desactívalo. |

## Desarrollo
```bash
pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen python -m pytest -q   # tests (también en Linux)
python main.py --selftest                       # comprueba dependencias
python build.py                                 # .exe con PyInstaller
```
Estructura:
- `app/controller.py`: estados del botón.
- `app/overlay.py`: icono, franja y fundidos.
- `app/capture.py`: captura y zona.
- `app/region_picker.py`: selector de zona.
- `app/gemini_client.py`: Interactions API, tiempos y precalentamiento.
- `app/input/`: mando con SDL2; ratón y teclado solo bajo demanda.
- `app/win32.py`: exclusión de captura, estilos y prioridad.
- `app/autostart.py`: arrancar con Windows.
- `app/settings_window.py`: la ventana de ajustes.
