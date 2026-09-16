from pathlib import Path
from typing import Callable, Optional

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .config import Config
from .signer import load_signer, sign_one_pdf
from .stamp import build_stamp_image

ProgressCallback = Callable[[int, int, str, str, str], None]


def resolve_page_index(sign_page, num_pages: int) -> int:
    if sign_page == "last":
        return -1
    idx = sign_page - 1
    if idx < 0 or idx >= num_pages:
        raise ValueError(
            f"SIGN_PAGE={sign_page} fuera de rango (el PDF tiene {num_pages} páginas)"
        )
    return idx


def list_pdfs(in_dir: Path) -> list:
    return sorted(in_dir.glob("*.pdf"))


def sign_batch(
    cfg: Config,
    password: str,
    on_progress: Optional[ProgressCallback] = None,
) -> list:
    """Firma todos los PDFs de cfg.in_dir y los deja en cfg.out_dir.

    Devuelve una lista de tuplas (nombre_archivo, "OK"|"ERROR", mensaje).
    on_progress, si se indica, se llama después de cada archivo con
    (hechos, total, nombre_archivo, status, mensaje).
    """
    pdfs = list_pdfs(cfg.in_dir)
    signer = load_signer(cfg.pfx_path, password.encode("utf-8"))

    resultados = []
    total = len(pdfs)
    for i, pdf_path in enumerate(pdfs, start=1):
        try:
            reader = PdfReader(str(pdf_path))
            num_pages = len(reader.pages)
            page_index = resolve_page_index(cfg.sign_page, num_pages)

            stamp_image = build_stamp_image(cfg)
            out_path = cfg.out_dir / pdf_path.name
            sign_one_pdf(pdf_path, out_path, cfg, stamp_image, page_index, signer)

            status, msg = "OK", ""
        except PdfReadError:
            status, msg = "ERROR", "PDF corrupto o ilegible"
        except ValueError as e:
            status, msg = "ERROR", str(e)
        except Exception as e:
            status, msg = "ERROR", f"{type(e).__name__}: {e}"

        resultados.append((pdf_path.name, status, msg))
        if on_progress:
            on_progress(i, total, pdf_path.name, status, msg)

    return resultados
