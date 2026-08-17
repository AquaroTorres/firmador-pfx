# Firmador PDF en masa

Programa que firma automáticamente todos los PDFs de una carpeta usando tu
certificado digital (`.pfx`), agregando además un sello visual con tu nombre
y la fecha de firma.

## Instalación en Windows (guía rápida)

### 1. Descarga el programa

Entra a la sección **[Releases](../../releases)** y descarga
**[firmador.exe](https://github.com/AquaroTorres/firmador-pfx/releases/download/v1.0.0/firmador.exe)**.

### 2. Crea la carpeta de trabajo

Crea una carpeta en tu computador (por ejemplo `Firmador` en el Escritorio) y
mueve ahí el `firmador.exe` descargado. Dentro de esa carpeta crea estas 4
carpetas: `assets`, `certs`, `in` y `out`. Al final debe verse así:

```
Firmador/
├── assets/
│   └── tu-firma.png
├── certs/
│   └── tu-certificado.pfx
├── config.env
├── in/
├── out/
└── firmador.exe
```

### 3. Copia tus archivos

- Copia tu certificado digital dentro de `certs/` (el archivo `.pfx` que te
  dieron).
- Copia la imagen de tu firma/sello dentro de `assets/` (por ejemplo
  `tu-firma.png`).

### 4. Crea tu configuración

Descarga
**[config.env.example](https://raw.githubusercontent.com/AquaroTorres/firmador-pfx/main/config.env.example)**,
guárdalo en la carpeta `Firmador` y renómbralo a `config.env`. Ábrelo con el
Bloc de notas y completa al menos estos datos:

| En `config.env` | Qué poner |
|---|---|
| `PFX_PATH` | `./certs/tu-certificado.pfx` (el nombre real de tu archivo) |
| `IMAGE_PATH` | `./assets/tu-firma.png` (el nombre real de tu imagen) |
| `SIGNER_FIRST_NAME` | Tu(s) nombre(s) |
| `SIGNER_LAST_NAME` | Tu(s) apellido(s) |

Guarda el archivo. El resto de las opciones ya vienen con valores que
funcionan; si quieres ajustar la posición o tamaño del sello, mira la
[configuración avanzada](#configuración-avanzada-opcional) más abajo.

### 5. Usa el programa

1. Coloca los PDFs que quieres firmar dentro de la carpeta `in/`.
2. Haz doble clic en `firmador.exe`.
3. Si no guardaste la clave del certificado en `config.env`, el programa te
   la va a pedir (no se muestra en pantalla mientras la escribes).
4. Al terminar, tus PDFs firmados van a estar en la carpeta `out/`, con el
   mismo nombre que tenían en `in/`.

Verás un resumen al final indicando qué archivos se firmaron bien (`OK`) y
cuáles fallaron (`ERROR`), con el motivo.

> **¿Windows bloquea el programa?** Si aparece un aviso de "Windows protegió
> tu PC", haz clic en **Más información** y luego en **Ejecutar de todas
> formas**. Esto pasa porque el `.exe` no está firmado por un desarrollador
> registrado en Microsoft; el programa es seguro y su código es público en
> este repositorio.

## ¿Usas macOS o Linux?

El proceso es el mismo (pasos 1 a 5), pero cambia el archivo que descargas y
cómo lo ejecutas:

- **macOS** (Apple Silicon: M1/M2/M3/M4): descarga
  [firmador-macos](https://github.com/AquaroTorres/firmador-pfx/releases/download/v1.0.0/firmador-macos),
  luego en una terminal, dentro de la carpeta del programa, ejecuta
  `chmod +x firmador-macos && ./firmador-macos`. La primera vez macOS puede
  bloquearlo por no tener firma de desarrollador — click derecho → Abrir, o
  ejecuta antes `xattr -d com.apple.quarantine firmador-macos`. Si tu Mac es
  Intel (no Apple Silicon), usa la
  [instalación desde código fuente](#instalación-desde-código-fuente).
- **Linux**: descarga
  [firmador-linux](https://github.com/AquaroTorres/firmador-pfx/releases/download/v1.0.0/firmador-linux)
  y ejecuta `chmod +x firmador-linux && ./firmador-linux`.

## Configuración avanzada (opcional)

Para la mayoría de los usuarios, los 4 datos del paso 4 son suficientes. Si
quieres ajustar la posición del sello, el texto o cómo se guarda la clave del
certificado, sigue leyendo.

### Clave del certificado

Se toma, en este orden: `--password` en la línea de comandos, luego
`PFX_PASSWORD` en `config.env` (si la definiste ahí), y si ninguna está
presente se pide de forma interactiva. Guardarla en `config.env` es más
cómodo pero menos seguro: cualquiera con acceso a ese archivo puede leerla;
solo hazlo si necesitas ejecutar el firmador sin interacción (ej. una tarea
programada).

### Posición y tamaño del sello

`POS_X`/`POS_Y`/`STAMP_WIDTH`/`STAMP_HEIGHT` (en `config.env`) ubican el sello
**dentro de la página del PDF**, en puntos PDF (72 puntos = 1 pulgada), medidos
desde la **esquina inferior izquierda de la página**:

![Coordenadas del sello en la página PDF](docs/posicion_firma.png)

- `POS_X`/`POS_Y` = esquina inferior izquierda del sello.
- `STAMP_WIDTH`/`STAMP_HEIGHT` = ancho y alto del sello, creciendo hacia la
  derecha y hacia arriba desde ese punto.

**Importante — proporción de la imagen**: `STAMP_WIDTH`/`STAMP_HEIGHT` deben
mantener la misma relación de aspecto (ancho:alto) que tu imagen real en
`IMAGE_PATH`, porque el sello se ajusta exactamente a esa caja sin recortar ni
preservar proporciones automáticamente — si no coinciden, la imagen se ve
estirada o achatada. La plantilla de ejemplo (`assets/firma-template.png`)
mide 754×185 px (relación ≈ 4,08:1); por eso `config.env.example` usa
`STAMP_WIDTH=180` / `STAMP_HEIGHT=44` (relación ≈ 4,09:1). Si usas tu propia
imagen, calcula `STAMP_HEIGHT = STAMP_WIDTH / (ancho_px / alto_px)`.

### Texto sobre el sello (nombre, apellido y fecha)

Sobre esa misma imagen se dibujan 3 líneas de texto, en píxeles de la imagen
(no de la página): nombres y apellidos (mismo tamaño, `NAME_FONT_SIZE`,
apilados uno debajo del otro desde `NAME_POS_X`/`NAME_POS_Y`) y la fecha de
firma (tamaño independiente `DATE_FONT_SIZE`, normalmente menor, desde
`DATE_POS_X`/`DATE_POS_Y`), con el huso horario local agregado
automáticamente (ej. `2026-08-05 18:59:04 -04:00`).

Otras variables relacionadas en `config.env`:

| Variable | Descripción |
|---|---|
| `SIGN_PAGE` | Página a firmar: número (1-based) o `last` |
| `DATE_FORMAT` | Formato de la fecha (sintaxis `strftime`), antes de agregar el huso horario |
| `FONT_PATH` | Ruta a una fuente `.ttf`/`.otf` propia (opcional; vacío usa la fuente por defecto) |
| `TEXT_COLOR` | Color del texto en RGB, formato `R,G,B` (ej. `0,0,0` para negro) |
| `SIGN_REASON` / `SIGN_LOCATION` / `SIGN_CONTACT_INFO` | Metadatos de la firma digital (no visibles en el sello, sí en las propiedades de firma del PDF) |

### Parámetros opcionales de línea de comandos

Sobrescriben lo definido en `config.env` sin tener que editarlo:

| Flag | Equivale a | Descripción |
|---|---|---|
| `--config RUTA` | — | Usar otro archivo de configuración |
| `--password CLAVE` | `PFX_PASSWORD` | Clave del PFX |
| `--sign-page` | `SIGN_PAGE` | Página a firmar: número (1-based) o `last` |
| `--pos-x` / `--pos-y` | `POS_X` / `POS_Y` | Posición del sello en la página |
| `--stamp-width` / `--stamp-height` | `STAMP_WIDTH` / `STAMP_HEIGHT` | Tamaño del sello en la página |

## Información técnica

Esta sección es para desarrolladores que quieran compilar el programa o
modificar el código.

### Compilación y releases automáticos

Cada vez que se publica un tag de versión (`vX.Y.Z`) en el repositorio,
[GitHub Actions](.github/workflows/build-executables.yml) compila
automáticamente los ejecutables de Windows, macOS y Linux en runners reales
de cada sistema operativo — necesario porque PyInstaller no cross-compila
entre sistemas y algunas dependencias (`cryptography`, `lxml`) requieren
compilarse en el sistema destino — y los publica en la sección
[Releases](../../releases) del repositorio. El runner de macOS de GitHub es
Apple Silicon (arm64), por eso ese binario no corre en Macs con procesador
Intel.

### Instalación desde código fuente

Para desarrollar o compilar el ejecutable tú mismo.

**Requisitos**: Python 3.10 o superior.

```bash
git clone git@github.com:AquaroTorres/firmador-pfx.git
cd firmador-pfx
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/requirements.txt
```

Se ejecuta con `python3 firmador.py` (mismas opciones y `config.env` que en
la sección [Instalación](#instalación-en-windows-guía-rápida)).

**Estructura del proyecto**:

```
firmador-pfx/
├── firmador.py           # entry point: python3 firmador.py
├── README.md
├── config.env.example     # plantilla de configuración
├── config.env             # tu configuración (no versionado)
├── src/                   # código (config, sello, firma)
├── requirements/          # dependencias (runtime y empaquetado)
├── certs/                 # tu certificado .pfx (no versionado)
├── assets/                # tu imagen de firma
├── docs/                  # imágenes de este README
├── in/                    # PDFs a firmar
└── out/                   # PDFs firmados
```

**Compilar el ejecutable localmente**:

```bash
pip install -r requirements/requirements-build.txt
pyinstaller --onefile --name firmador firmador.py
```

Esto genera `dist/firmador` (o `dist/firmador.exe` en Windows) para el
sistema operativo en el que lo ejecutes. El binario espera `config.env` y las
carpetas `certs/`, `assets/`, `in/` y `out/` junto a él (rutas relativas al
propio ejecutable, no al directorio desde el que se invoque).

### Tecnología usada

- **[Python](https://www.python.org/)** 3.10+
- **[pyHanko](https://github.com/MatthiasValvekens/pyHanko)** — firma digital PAdES con certificados PKCS#12 (`.pfx`) y estampado visual
- **[Pillow](https://python-pillow.org/)** — composición del sello (nombre, apellido y fecha sobre la imagen de plantilla)
- **[pypdf](https://pypdf.readthedocs.io/)** — lectura de metadatos del PDF (conteo de páginas) y detección de archivos corruptos
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — parseo del archivo de configuración `config.env`
- **[PyInstaller](https://pyinstaller.org/)** — empaquetado como ejecutable standalone (sin requerir Python instalado)
- **[GitHub Actions](.github/workflows/build-executables.yml)** — compila y publica automáticamente los ejecutables de Windows, macOS y Linux al crear un tag de versión
