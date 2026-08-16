from dataclasses import dataclass
from pathlib import Path
import sys
from dotenv import dotenv_values


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


@dataclass
class Config:
    in_dir: Path
    out_dir: Path
    pfx_path: Path
    sign_page: "str | int"
    pos_x: int
    pos_y: int
    stamp_width: int
    stamp_height: int
    image_path: Path
    signer_first_name: str
    signer_last_name: str
    name_font_size: int
    name_pos_x: int
    name_pos_y: int
    date_format: str
    date_font_size: int
    date_pos_x: int
    date_pos_y: int
    font_path: "str | None"
    text_color: tuple
    sign_reason: "str | None"
    sign_location: "str | None"
    sign_contact_info: "str | None"


def _resolve(base: Path, raw: str) -> Path:
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (base / p).resolve()


def _req(raw: dict, key: str, config_path: Path) -> str:
    v = raw.get(key)
    if not v:
        raise ValueError(
            f"Falta configurar '{key}' en {config_path}.\n"
            f"  Agrega una línea como '{key}=...' en ese archivo y vuelve a intentar."
        )
    return v


def _require_path(base: Path, raw: dict, key: str, config_path: Path, label: str, kind: str) -> Path:
    raw_value = _req(raw, key, config_path)
    resolved = _resolve(base, raw_value)
    exists = resolved.is_dir() if kind == "dir" else resolved.is_file()
    if not exists:
        raise ValueError(
            f"No se encontró {label}.\n"
            f"  Valor en {config_path.name}: {key}={raw_value}\n"
            f"  Ruta buscada: {resolved}\n"
            f"  Revisa que la ruta sea correcta (relativa a {base}) y que el archivo/carpeta exista."
        )
    return resolved


def load_config(config_path: str) -> Config:
    config_path = Path(config_path).resolve()
    if not config_path.is_file():
        raise ValueError(
            f"No se encontró el archivo de configuración: {config_path}\n"
            f"  Copia 'config.env.example' a 'config.env' (o indica la ruta correcta con --config)."
        )

    raw = dotenv_values(config_path)
    base = app_dir()

    in_dir = _require_path(base, raw, "IN_DIR", config_path, "la carpeta de entrada (IN_DIR)", "dir")
    pfx_path = _require_path(base, raw, "PFX_PATH", config_path, "el certificado PFX (PFX_PATH)", "file")
    image_path = _require_path(base, raw, "IMAGE_PATH", config_path, "la imagen de la firma (IMAGE_PATH)", "file")

    sign_page_raw = _req(raw, "SIGN_PAGE", config_path).strip().lower()
    sign_page = "last" if sign_page_raw == "last" else int(sign_page_raw)

    text_color_raw = raw.get("TEXT_COLOR", "0,0,0")
    text_color = tuple(int(c.strip()) for c in text_color_raw.split(","))

    return Config(
        in_dir=in_dir,
        out_dir=_resolve(base, raw.get("OUT_DIR", "./out")),
        pfx_path=pfx_path,
        sign_page=sign_page,
        pos_x=int(_req(raw, "POS_X", config_path)),
        pos_y=int(_req(raw, "POS_Y", config_path)),
        stamp_width=int(_req(raw, "STAMP_WIDTH", config_path)),
        stamp_height=int(_req(raw, "STAMP_HEIGHT", config_path)),
        image_path=image_path,
        signer_first_name=_req(raw, "SIGNER_FIRST_NAME", config_path),
        signer_last_name=_req(raw, "SIGNER_LAST_NAME", config_path),
        name_font_size=int(raw.get("NAME_FONT_SIZE", 28)),
        name_pos_x=int(raw.get("NAME_POS_X", 0)),
        name_pos_y=int(raw.get("NAME_POS_Y", 0)),
        date_format=raw.get("DATE_FORMAT", "%d-%m-%Y %H:%M:%S"),
        date_font_size=int(raw.get("DATE_FONT_SIZE", 18)),
        date_pos_x=int(raw.get("DATE_POS_X", 0)),
        date_pos_y=int(raw.get("DATE_POS_Y", 0)),
        font_path=raw.get("FONT_PATH") or None,
        text_color=text_color,
        sign_reason=raw.get("SIGN_REASON") or None,
        sign_location=raw.get("SIGN_LOCATION") or None,
        sign_contact_info=raw.get("SIGN_CONTACT_INFO") or None,
    )
