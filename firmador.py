import argparse
import getpass
import logging
import sys
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from config import app_dir, load_config
from stamp import build_stamp_image
from signer import load_signer, sign_one_pdf

# pyHanko registra en el logger los errores de carga del PFX con traceback
# incluido antes de devolver None; ya los reportamos con un mensaje propio,
# así que se sube el nivel para no duplicar ruido en la salida.
logging.getLogger("pyhanko").setLevel(logging.CRITICAL)


def resolve_page_index(sign_page, num_pages: int) -> int:
    if sign_page == "last":
        return -1
    idx = sign_page - 1
    if idx < 0 or idx >= num_pages:
        raise ValueError(
            f"SIGN_PAGE={sign_page} fuera de rango (el PDF tiene {num_pages} páginas)"
        )
    return idx


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Firmador de PDFs en lote con certificado PFX (firma PAdES)."
    )
    parser.add_argument(
        "--config",
        default=str(app_dir() / "config.env"),
        help="Ruta al archivo de configuración .env (default: config.env junto al ejecutable)",
    )
    parser.add_argument("--password", help="Clave del certificado PFX")
    parser.add_argument("--sign-page", help="Página a firmar: entero 1-based o 'last'")
    parser.add_argument("--pos-x", type=int, help="Posición X del sello en el PDF (puntos)")
    parser.add_argument("--pos-y", type=int, help="Posición Y del sello en el PDF (puntos)")
    parser.add_argument("--stamp-width", type=int, help="Ancho del sello en el PDF (puntos)")
    parser.add_argument("--stamp-height", type=int, help="Alto del sello en el PDF (puntos)")
    return parser


def apply_overrides(cfg, args) -> None:
    if args.sign_page is not None:
        raw = args.sign_page.strip().lower()
        cfg.sign_page = "last" if raw == "last" else int(raw)
    if args.pos_x is not None:
        cfg.pos_x = args.pos_x
    if args.pos_y is not None:
        cfg.pos_y = args.pos_y
    if args.stamp_width is not None:
        cfg.stamp_width = args.stamp_width
    if args.stamp_height is not None:
        cfg.stamp_height = args.stamp_height


def main() -> int:
    args = build_arg_parser().parse_args()

    try:
        cfg = load_config(args.config)
    except ValueError as e:
        print(f"No se pudo iniciar el firmador:\n{e}")
        return 1

    apply_overrides(cfg, args)

    pdfs = sorted(cfg.in_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No se encontraron PDFs en {cfg.in_dir}")
        return 0

    password = args.password or getpass.getpass(f"Clave del certificado {cfg.pfx_path.name}: ")

    try:
        signer = load_signer(cfg.pfx_path, password.encode("utf-8"))
    except ValueError as e:
        print(f"No se pudo iniciar el firmador:\n{e}")
        return 1

    resultados = []
    for pdf_path in pdfs:
        try:
            reader = PdfReader(str(pdf_path))
            num_pages = len(reader.pages)
            page_index = resolve_page_index(cfg.sign_page, num_pages)

            stamp_image = build_stamp_image(cfg)
            out_path = cfg.out_dir / pdf_path.name
            sign_one_pdf(pdf_path, out_path, cfg, stamp_image, page_index, signer)

            resultados.append((pdf_path.name, "OK", ""))
        except PdfReadError:
            resultados.append((pdf_path.name, "ERROR", "PDF corrupto o ilegible"))
        except ValueError as e:
            resultados.append((pdf_path.name, "ERROR", str(e)))
        except Exception as e:
            resultados.append((pdf_path.name, "ERROR", f"{type(e).__name__}: {e}"))

    print("\n--- Resumen del batch ---")
    ok = sum(1 for _, status, _ in resultados if status == "OK")
    for name, status, msg in resultados:
        line = f"[{status}] {name}"
        if msg:
            line += f" - {msg}"
        print(line)
    print(f"\nTotal: {len(resultados)}  OK: {ok}  Fallidos: {len(resultados) - ok}")

    return 0 if ok == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
