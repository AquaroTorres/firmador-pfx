import argparse
import getpass
import logging
import sys

from src.batch import list_pdfs, sign_batch
from src.config import app_dir, load_config

# pyHanko registra en el logger los errores de carga del PFX con traceback
# incluido antes de devolver None; ya los reportamos con un mensaje propio,
# así que se sube el nivel para no duplicar ruido en la salida.
logging.getLogger("pyhanko").setLevel(logging.CRITICAL)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Firmador de PDFs en lote con certificado PFX (firma PAdES)."
    )
    parser.add_argument(
        "--config",
        default=str(app_dir() / "config.env"),
        help="Ruta al archivo de configuración .env (default: config.env junto al ejecutable)",
    )
    parser.add_argument(
        "--password",
        help="Clave del certificado PFX (si no se indica, se usa PFX_PASSWORD del config "
        "o se pide de forma interactiva)",
    )
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

    if not list_pdfs(cfg.in_dir):
        print(f"No se encontraron PDFs en {cfg.in_dir}")
        return 0

    password = (
        args.password
        or cfg.pfx_password
        or getpass.getpass(f"Clave del certificado {cfg.pfx_path.name}: ")
    )

    try:
        resultados = sign_batch(cfg, password)
    except ValueError as e:
        print(f"No se pudo iniciar el firmador:\n{e}")
        return 1

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
