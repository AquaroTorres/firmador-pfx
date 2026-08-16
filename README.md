# Firmador PDF en masa

Firma digitalmente (PAdES) todos los PDFs de una carpeta usando un certificado
`.pfx`/`.p12`, estampando visualmente un sello con nombre, apellido y fecha de
firma generados automáticamente sobre una imagen de plantilla.

## 1. Instalación

**Estructura del proyecto**:

```
firmador-pfx/
├── firmador.py           # ejecutable: python3 firmador.py
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

### Opción A: usar el ejecutable ya compilado (sin instalar Python)

Cada vez que se publica un tag de versión (`vX.Y.Z`) en el repositorio,
[GitHub Actions](.github/workflows/build-executables.yml) compila
automáticamente los ejecutables de Windows y Linux y los deja disponibles en
la sección **[Releases](../../releases)** del repositorio:

- **Windows**: descarga `firmador-windows` (contiene `firmador.exe`).
- **Linux**: descarga `firmador-linux` (contiene `firmador`).

Pasos:

1. Descarga el ejecutable de tu sistema desde Releases y colócalo en una
   carpeta propia.
2. Junto a él, copia `config.env.example` → `config.env` (ajustado a tus
   datos) y las carpetas `certs/`, `assets/`, `in/` y `out/` — ver
   [Configuración](#configuración) más abajo.
3. Ejecútalo:
   - **Windows**: doble clic en `firmador.exe`, o desde una consola
     `firmador.exe`.
   - **Linux**: `chmod +x firmador && ./firmador`.

No necesitas tener Python instalado para esta opción.

### Opción B: instalar desde el código fuente (Python)

**Requisitos**: Python 3.10 o superior.

```bash
git clone git@github.com:AquaroTorres/firmador-pfx.git
cd firmador-pfx
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/requirements.txt
```

Se ejecuta con `python3 firmador.py` (ver sección [Uso](#2-uso)).

### Configuración

- Certificado digital en `certs/tu-certificado.pfx`.
- Imagen de la firma (plantilla) en `assets/tu-firma.png`.
- Copia `config.env.example` a `config.env` y ajusta las rutas y valores a los tuyos:

```bash
cp config.env.example config.env
```

`config.env` **no se sube a git** (está en `.gitignore`) porque referencia tu
certificado y tus datos personales — cada persona/organización mantiene el suyo.

### Compilar el ejecutable tú mismo (opcional)

Los ejecutables de Releases ya cubren esto para Windows y Linux, pero también
puedes generarlo localmente:

```bash
pip install -r requirements/requirements-build.txt
pyinstaller --onefile --name firmador firmador.py
```

Esto genera `dist/firmador` (o `dist/firmador.exe` en Windows) para el
sistema operativo en el que lo ejecutes — PyInstaller no cross-compila entre
sistemas, por eso el build de Windows se hace en un runner de GitHub Actions
en vez de generarse desde Linux/Mac. El binario espera `config.env` y las
carpetas `certs/`, `assets/`, `in/` y `out/` junto a él (rutas relativas al
propio ejecutable, no al directorio desde el que se invoque), así que
cópialo a la raíz del proyecto para usarlo, o copia esos archivos/carpetas
junto al binario si lo distribuyes por separado.

## 2. Uso

1. Coloca los PDFs a firmar en `in/`.
2. Ejecuta:

   ```bash
   python3 firmador.py
   ```

   (o `./firmador` / `firmador.exe` si usas el ejecutable descargado de
   Releases, o `./dist/firmador` si lo compilaste tú mismo).
3. La clave del certificado se toma, en este orden: `--password`, luego
   `PFX_PASSWORD` en `config.env` (si la definiste ahí), y si ninguna está
   presente se pide de forma interactiva (no queda visible en pantalla).
   Guardarla en `config.env` es más cómodo pero menos seguro: cualquiera con
   acceso a ese archivo puede leerla; solo hazlo si necesitas ejecutar el
   firmador sin interacción (ej. una tarea programada).
4. Los PDFs firmados quedan en `out/`, con el mismo nombre que en `in/`. Al
   final se imprime un resumen `[OK]`/`[ERROR]` por archivo.

**Parámetros de línea de comandos** (sobrescriben lo definido en `config.env`
sin tener que editarlo):

| Flag | Equivale a | Descripción |
|---|---|---|
| `--config RUTA` | — | Usar otro archivo de configuración |
| `--password CLAVE` | `PFX_PASSWORD` | Clave del PFX |
| `--sign-page` | `SIGN_PAGE` | Página a firmar: número (1-based) o `last` |
| `--pos-x` / `--pos-y` | `POS_X` / `POS_Y` | Posición del sello en la página |
| `--stamp-width` / `--stamp-height` | `STAMP_WIDTH` / `STAMP_HEIGHT` | Tamaño del sello en la página |

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
estirada o achatada. La plantilla incluida (`assets/firma-template.png`) mide
754×185 px (relación ≈ 4,08:1); por eso el ejemplo en `config.env.example`
usa `STAMP_WIDTH=180` / `STAMP_HEIGHT=44` (relación ≈ 4,09:1). Si usas tu
propia imagen, calcula `STAMP_HEIGHT = STAMP_WIDTH / (ancho_px / alto_px)`.

Aparte, dentro de esa misma imagen se dibujan 3 líneas de texto en píxeles de
la imagen (no de la página): nombres y apellidos (mismo tamaño,
`NAME_FONT_SIZE`, apilados uno debajo del otro desde `NAME_POS_X`/`NAME_POS_Y`)
y la fecha de firma (tamaño independiente `DATE_FONT_SIZE`, normalmente menor,
desde `DATE_POS_X`/`DATE_POS_Y`), con el huso horario local agregado
automáticamente (ej. `2026-08-05 18:59:04 -04:00`).

## 3. Tecnología usada

- **[Python](https://www.python.org/)** 3.10+
- **[pyHanko](https://github.com/MatthiasValvekens/pyHanko)** — firma digital PAdES con certificados PKCS#12 (`.pfx`) y estampado visual
- **[Pillow](https://python-pillow.org/)** — composición del sello (nombre, apellido y fecha sobre la imagen de plantilla)
- **[pypdf](https://pypdf.readthedocs.io/)** — lectura de metadatos del PDF (conteo de páginas) y detección de archivos corruptos
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — parseo del archivo de configuración `config.env`
- **[PyInstaller](https://pyinstaller.org/)** — empaquetado como ejecutable standalone (sin requerir Python instalado)
- **[GitHub Actions](.github/workflows/build-executables.yml)** — compila y publica automáticamente los ejecutables de Windows y Linux al crear un tag de versión
