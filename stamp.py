from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config import Config

# Separación entre la línea de nombres y la de apellidos, como múltiplo del
# tamaño de fuente (interlineado tipográfico típico).
NAME_LINE_SPACING = 1.25


def _load_font(font_path, size):
    if font_path:
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default(size=size)


def _format_date_with_offset(now: datetime, date_format: str) -> str:
    text = now.strftime(date_format)
    offset = now.strftime("%z")  # ej. "-0400"
    if offset:
        text += f" {offset[:3]}:{offset[3:]}"  # ej. " -04:00"
    return text


def build_stamp_image(cfg: Config, now: "datetime | None" = None) -> Image.Image:
    now = (now or datetime.now()).astimezone()
    base = Image.open(cfg.image_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    name_font = _load_font(cfg.font_path, cfg.name_font_size)
    date_font = _load_font(cfg.font_path, cfg.date_font_size)

    line_height = round(cfg.name_font_size * NAME_LINE_SPACING)
    draw.text((cfg.name_pos_x, cfg.name_pos_y), cfg.signer_first_name, font=name_font, fill=cfg.text_color)
    draw.text(
        (cfg.name_pos_x, cfg.name_pos_y + line_height),
        cfg.signer_last_name,
        font=name_font,
        fill=cfg.text_color,
    )

    date_text = _format_date_with_offset(now, cfg.date_format)
    draw.text((cfg.date_pos_x, cfg.date_pos_y), date_text, font=date_font, fill=cfg.text_color)

    return base
