# DO IT · Generador de Reportes de Satisfacción
## Guía de uso paso a paso

---

## 1. Requisitos previos (solo la primera vez)

Antes de usar el generador necesitas tener **Python 3.12 o superior** instalado en tu computador. Esto solo se hace una vez.

### Si usas Mac

**Paso 1 — Abre Terminal**

Búscalo en **Aplicaciones → Utilidades → Terminal**. También puedes buscarlo con Spotlight: presiona `Cmd + Espacio`, escribe "Terminal" y presiona Enter.

**Paso 2 — Verifica si ya tienes Python 3.12+**

Escribe lo siguiente y presiona Enter:

    python3 --version

Deberías ver algo así:

    Python 3.12.4

Si el número empieza por 3.12 o superior (3.13, 3.14, etc.), ya lo tienes. Salta a la sección 2.

Si ves un número menor (3.9, 3.10, 3.11) o un error como `command not found`, instálalo en el paso 3.

**Paso 3 — Instala Python 3.12+**

1. Abre tu navegador y ve a: **https://www.python.org/downloads/**
2. Haz clic en el botón amarillo grande que dice **"Download Python 3.12.x"** (o la versión más reciente que aparezca)
3. Se descargará un archivo `.pkg`. Ábrelo y sigue las instrucciones del instalador (solo dale "Continuar" y "Instalar")
4. Cuando termine, **cierra Terminal y vuélvelo a abrir**
5. Escribe `python3 --version` y confirma que dice `Python 3.12.x` o superior

**¿Qué versión descargo?** Siempre la que aparece en el botón amarillo de python.org/downloads. A marzo de 2026, la versión recomendada es Python 3.12.4 o superior.


### Si usas Windows

**Paso 1 — Verifica si ya tienes Python 3.12+**

Abre el menú Inicio, busca **"cmd"** y abre **Símbolo del sistema**. Escribe lo siguiente y presiona Enter:

    python --version

Deberías ver algo así:

    Python 3.12.4

Si el número empieza por 3.12 o superior, ya lo tienes. Salta a la sección 2.

Si ves un error o una versión menor, instálalo en el paso 2.

**Paso 2 — Instala Python 3.12+**

1. Abre tu navegador y ve a: **https://www.python.org/downloads/**
2. Haz clic en el botón amarillo grande que dice **"Download Python 3.12.x"**
3. Abre el archivo descargado (`.exe`)
4. **⚠️ MUY IMPORTANTE:** En la primera pantalla del instalador, **MARCA la casilla que dice "Add Python to PATH"** (está abajo). Sin esto, el generador NO funcionará.
5. Haz clic en **"Install Now"** y espera a que termine
6. **Reinicia tu computador**
7. Abre de nuevo cmd y escribe `python --version` para confirmar


---

## 2. Descarga y ubica la carpeta del generador

1. Descomprime el archivo **DO_IT_Generador_Reportes.zip** que recibiste
2. Coloca la carpeta `doit_report` donde prefieras (por ejemplo, en tu **Escritorio**)
3. **No cambies el nombre de los archivos** ni muevas cosas dentro de la carpeta


---

## 3. Abre el generador

### En Windows

Abre la carpeta `doit_report` y haz **doble clic** en el archivo:

    📄 Generar Reporte.bat

Se abrirá una ventana negra brevemente y luego aparecerá la interfaz del generador. La primera vez puede tardar unos segundos mientras se instalan componentes automáticamente.

Si la ventana se cierra inmediatamente, ve a la sección de "Solución de problemas" al final de esta guía.

### En Mac

Abre la carpeta `doit_report` y haz **doble clic** en el archivo:

    📄 Generar Reporte.command

La primera vez, macOS puede mostrar una advertencia de seguridad. Si esto pasa:
1. Haz clic derecho (o Control + clic) en `Generar Reporte.command`
2. Selecciona **"Abrir"** en el menú
3. En la ventana de advertencia, haz clic en **"Abrir"** de nuevo

A partir de la segunda vez, se abrirá con doble clic sin problemas.

**Si el archivo .command no funciona** (alternativa por Terminal):
1. Abre Terminal
2. Escribe `cd ` (con espacio), arrastra la carpeta `doit_report` desde Finder a la ventana de Terminal, y presiona Enter
3. Escribe: `./"Generar Reporte.sh"` y presiona Enter


---

## 4. Genera tu primer reporte

Una vez abierta la interfaz, verás la pestaña **"⚡ Generar Reporte"**. Llena los siguientes campos:

| # | Campo | Qué poner | Ejemplo |
|---|-------|-----------|---------|
| 1 | **Nombre del taller** | El nombre completo del taller | Cómo lograr resultados ágilmente |
| 2 | **Duración** | Cuánto duró | 8 horas |
| 3 | **Lugar** | Ciudad o sede | Bogotá, Colombia |
| 4 | **Total participantes** | Cuántas personas asistieron al taller (no solo los que evaluaron). Si lo dejas vacío, se usa el número de evaluaciones del CSV | 25 |
| 5 | **Segundo instructor/a** | *(Opcional)* Si hubo dos facilitadores, escribe aquí el nombre del segundo. El primero se toma del CSV. Déjalo vacío si solo hubo uno | María López |
| 6 | **CSV de encuesta** | El archivo .csv exportado de Fillout | *(botón Seleccionar)* |
| 7 | **Logo del cliente** | El logo de la empresa en PNG o JPG | *(botón Seleccionar)* |
| 8 | **Fotos del taller** | Entre 2 y 4 fotos en JPG o PNG | *(botón Seleccionar)* |

### Pasos:

1. Llena los campos de texto: nombre del taller, duración, lugar
2. Si asistieron más personas de las que evaluaron, escribe el total en **"Total participantes"**
3. Si hubo un segundo instructor, escribe su nombre
4. Haz clic en **"Seleccionar"** junto a cada archivo:
   - **CSV de encuesta:** busca el archivo .csv exportado de Fillout
   - **Logo del cliente:** busca el logo de la empresa
   - **Fotos del taller:** selecciona 2 a 4 fotos (mantén `Ctrl` en Windows o `Cmd` en Mac para seleccionar varias)
5. Haz clic en el botón dorado **⚡ GENERAR REPORTE**
6. Espera unos segundos. Verás un mensaje verde con las rutas de los archivos generados
7. Haz clic en los botones para abrir el PDF, copiar el link del HTML, o ver la imagen

### ¿Qué archivos se generan?

El generador crea **3 archivos** automáticamente:

| Archivo | Para qué sirve | Dónde queda |
|---------|----------------|-------------|
| **PDF** | Reporte completo descargable. Para enviar como adjunto o imprimir | `salida/` |
| **HTML** | Página web con link compartible. Para que el cliente vea los resultados online | `salida/` (con link copiable) |
| **Imagen** | Preview visual de alta resolución. Para enviar por correo o WhatsApp, linkeada al HTML | `salida/` |

La **imagen** está pensada para enviarse por correo linkeada al reporte HTML: el destinatario hace clic en la imagen y se abre el reporte completo en el navegador.


---

## 5. Configura los datos del gerente comercial

La primera vez (o cuando cambie la persona de contacto), configura los datos que aparecen en la última página del reporte y en la sección "Revisemos juntos los resultados":

1. Haz clic en la pestaña **"⚙ Configuración"**
2. Llena los campos:
   - **Nombre** del gerente comercial
   - **Email**
   - **Teléfono**
   - **Web**
3. Haz clic en **"💾 Guardar configuración"**

Estos datos se guardan en `config.json` y se usan automáticamente en todos los reportes futuros.


---

## 6. Cambiar el QR de WhatsApp

El QR que aparece en la tarjeta de contacto del reporte (PDF y HTML) se puede actualizar:

1. Ve a la carpeta `doit_report/assets/`
2. Reemplaza el archivo **`qr_gerente.png`** con tu nuevo QR
3. Asegúrate de que se llame **exactamente** `qr_gerente.png`
4. El nuevo QR aparecerá automáticamente en el próximo reporte

**Tip:** usa una imagen cuadrada para que se vea bien dentro del círculo del PDF.


---

## 7. Cómo exportar el CSV desde Fillout

1. Entra a tu cuenta de **Fillout** (fillout.com)
2. Abre el formulario de satisfacción del taller
3. Ve a la pestaña de **Respuestas** (o "Responses")
4. Haz clic en **Exportar** / **Export** (arriba a la derecha)
5. Selecciona formato **CSV**
6. Guarda el archivo en tu computador
7. Usa ese archivo en el campo **"CSV de encuesta"** del generador


---

## 8. Cómo se comparte el reporte

El generador crea 3 archivos cada vez que generas un reporte. Así se usa cada uno:

**📄 PDF** — Es el reporte formal completo. Envíalo como adjunto de correo, o imprímelo para entregar al cliente en persona.

**🌐 HTML** — Es una página web con un link único (incluye la fecha para evitar duplicados entre cursos del mismo cliente). Copia el link y compártelo por correo, Slack o WhatsApp. El cliente abre el link y ve el reporte completo en el navegador.

**🖼️ Imagen de preview** — Es una imagen de alta resolución que resume los resultados principales. El flujo recomendado es:
1. Inserta la imagen en el cuerpo de un correo o mensaje de WhatsApp
2. Linkea la imagen al URL del HTML
3. El destinatario ve el resumen visual, hace clic, y se abre el reporte completo

Este flujo permite que el cliente vea un preview atractivo antes de entrar al reporte detallado.


---

## Solución de problemas comunes

**"Python no instalado" o "python no se reconoce como comando"**
→ Revisa la sección 1. En Windows, asegúrate de haber marcado **"Add Python to PATH"** durante la instalación. Si ya lo instalaste sin esa casilla, desinstálalo y vuélvelo a instalar marcándola. Reinicia el computador después.

**¿Qué versión de Python descargo?**
→ Ve a **python.org/downloads** y descarga la que aparece en el botón amarillo grande. Necesitas **3.12 o superior**.

**La ventana se abre y se cierra inmediatamente (Windows)**
→ Abre Símbolo del sistema (busca "cmd" en el menú Inicio), navega a la carpeta con `cd Escritorio\doit_report` (o donde la tengas) y escribe `python app.py`. Esto mostrará el error específico.

**En Mac, el archivo .command muestra "no se puede verificar el desarrollador"**
→ Haz clic derecho → Abrir → "Abrir" en la advertencia. Solo pasa la primera vez.

**En Mac, el .sh se abre en un editor de texto en vez de ejecutarse**
→ Usa el archivo `.command` en su lugar (ver sección 3), o abre Terminal manualmente y ejecútalo desde ahí.

**"Selecciona el archivo CSV" aparece en rojo**
→ Necesitas seleccionar el archivo CSV antes de generar. Haz clic en "Seleccionar" junto a "CSV de encuesta".

**El logo del cliente tiene fondo negro en el PDF**
→ No hay problema. El generador elimina automáticamente los fondos negros de los logos.

**Las fotos se ven cortadas**
→ Es normal. Se recortan para mantener la proporción sin deformar. Usa fotos horizontales (paisaje) para mejor resultado.

**El título del taller no cabe en la imagen**
→ El generador ajusta automáticamente el tamaño del texto para títulos largos. Si aun así se ve apretado, intenta un nombre más corto.

**No veo el link del HTML después de generar**
→ El link aparece en la interfaz después de hacer clic en "Generar". Si no lo ves, revisa la carpeta `salida/` — el HTML estará ahí con un nombre que incluye el cliente y la fecha.


---

## Estructura de la carpeta (referencia)

    doit_report/
    ├── Generar Reporte.bat       ← Doble clic para abrir (Windows)
    ├── Generar Reporte.command   ← Doble clic para abrir (Mac)
    ├── Generar Reporte.sh        ← Alternativa Mac por Terminal
    ├── app.py                    ← La aplicación (no tocar)
    ├── pdf_engine.py             ← Motor de PDF (no tocar)
    ├── html_engine.py            ← Motor de HTML (no tocar)
    ├── image_engine.py           ← Motor de imagen (no tocar)
    ├── config.json               ← Datos del gerente comercial
    ├── Guia_de_Uso.pdf           ← Esta guía en PDF
    ├── assets/
    │   ├── logo_doit_light.png
    │   ├── logo_doit_dark.png
    │   ├── logo_vector.*         ← Logo DO IT en vector (para HTML)
    │   └── qr_gerente.png        ← QR de WhatsApp (reemplazable)
    ├── entrada/                  ← Archivos de ejemplo
    │   ├── datos_curso.csv
    │   └── logo_cliente.png
    ├── fotos_curso/              ← Fotos de ejemplo
    └── salida/                   ← Aquí aparecen los reportes generados
        ├── *.pdf
        ├── *.html
        └── *.png
