# Firmador PDF en masa

Firma digitalmente (PAdES) todos los PDFs de una carpeta usando un certificado
`.pfx`/`.p12`, estampando visualmente un sello con nombre, apellido y fecha de
firma generados automáticamente sobre una imagen de plantilla.

## 1. Instalación

1. Ve a la sección **[Releases](../../releases)** del repositorio y descarga
   el archivo de tu sistema operativo:
   - **Windows**: `firmador.exe`
   - **macOS** (Apple Silicon: M1/M2/M3/M4): `firmador-macos`
   - **Linux**: `firmador-linux`
2. Crea una carpeta para el firmador y coloca ahí el ejecutable descargado y dentro crea 4 carpetas, el resultado debe verse así:
```
firmador/               (o como hayas llamado a tu carpeta)
├── assets/
│   └── tu-firma.png
├── certs/
│   └── tu-certificado.pfx
├── config.env           # tu configuración (copiado desde config.env.example)
├── in/                  # PDFs a firmar
├── out/                 # PDFs firmados (se generan solos)
└── firmador.exe
```
3. Configúración:
   1. Copia tu certificado a `certs/tu-certificado.pfx`.
   2. Copia tu imagen de firma a `assets/tu-firma.png`.
   3. Copia `config.env.example` a `config.env` y ajusta las rutas y valores:
   4. Ejecútalo:
      - **Windows**: doble clic en `firmador.exe`, o desde una consola
        `firmador.exe`.
      - **macOS**: `chmod +x firmador-macos && ./firmador-macos`. Al ser un
        binario sin firma de desarrollador, macOS puede bloquearlo la primera
        vez ("no se puede abrir porque su desarrollador no pudo verificarse");
        click derecho → Abrir, o ejecuta antes
        `xattr -d com.apple.quarantine firmador-macos`. Si tienes un Mac con
        procesador Intel (no Apple Silicon), usa la
        [instalación avanzada](#instalación-avanzada-código-fuente) en su lugar.
      - **Linux**: `chmod +x firmador-linux && ./firmador-linux`.

Te va a pedir la clave del certificado si no la definiste en `config.env` (ver
más abajo). Los PDFs firmados quedan en `out/`, con el mismo nombre que
tenían en `in/`, y al final se imprime un resumen `[OK]`/`[ERROR]` por archivo.
### Clave del certificado

Se toma, en este orden: `--password` en la línea de comandos, luego
`PFX_PASSWORD` en `config.env` (si la definiste ahí), y si ninguna está
presente se pide de forma interactiva (no queda visible en pantalla).
Guardarla en `config.env` es más cómodo pero menos seguro: cualquiera con
acceso a ese archivo puede leerla; solo hazlo si necesitas ejecutar el
firmador sin interacción (ej. una tarea programada).

### Coordenadas y tamaño del sello

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

### Texto dinámico (nombre, apellido y fecha)

Sobre esa misma imagen se dibujan 3 líneas de texto, en píxeles de la imagen
(no de la página): nombres y apellidos (mismo tamaño, `NAME_FONT_SIZE`,
apilados uno debajo del otro desde `NAME_POS_X`/`NAME_POS_Y`) y la fecha de
firma (tamaño independiente `DATE_FONT_SIZE`, normalmente menor, desde
`DATE_POS_X`/`DATE_POS_Y`), con el huso horario local agregado
automáticamente (ej. `2026-08-05 18:59:04 -04:00`).

### Parámetros opcionales de línea de comandos

Sobrescriben lo definido en `config.env` sin tener que editarlo:

| Flag | Equivale a | Descripción |
|---|---|---|
| `--config RUTA` | — | Usar otro archivo de configuración |
| `--password CLAVE` | `PFX_PASSWORD` | Clave del PFX |
| `--sign-page` | `SIGN_PAGE` | Página a firmar: número (1-based) o `last` |
| `--pos-x` / `--pos-y` | `POS_X` / `POS_Y` | Posición del sello en la página |
| `--stamp-width` / `--stamp-height` | `STAMP_WIDTH` / `STAMP_HEIGHT` | Tamaño del sello en la página |

## 3. Información técnica

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

### Instalación avanzada (código fuente)

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
la sección [Instalación](#1-instalación)).

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
- **[GitHub Actions](.github/workflows/build-executables.yml)** — compila y publica automáticamente los ejecutables de Windows y Linux al crear un tag de versión
