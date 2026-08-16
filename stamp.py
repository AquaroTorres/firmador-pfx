from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

from config import Config


def _load_font(font_path, size):
    if font_path:
        return ImageFont.truetype(font_path, size)
    return ImageFont.load_default(size=size)


def build_stamp_image(cfg: Config, now: "datetime | None" = None) -> Image.Image:
    now = now or datetime.now()
    base = Image.open(cfg.image_path).convert("RGBA")
    draw = ImageDraw.Draw(base)

    name_font = _load_font(cfg.font_path, cfg.name_font_size)
    date_font = _load_font(cfg.font_path, cfg.date_font_size)

    full_name = f"{cfg.signer_first_name} {cfg.signer_last_name}"
    draw.text((cfg.name_pos_x, cfg.name_pos_y), full_name, font=name_font, fill=cfg.text_color)

    date_text = now.strftime(cfg.date_format)
    draw.text((cfg.date_pos_x, cfg.date_pos_y), date_text, font=date_font, fill=cfg.text_color)

    return base
