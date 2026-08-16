from pathlib import Path

from PIL import Image

from pyhanko import stamp
from pyhanko.pdf_utils import layout
from pyhanko.pdf_utils.images import PdfImage
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import fields, signers

from config import Config


def load_signer(pfx_path: Path, password: bytes) -> signers.SimpleSigner:
    # pyHanko's load_pkcs12 swallows load errors internally (logs them) and
    # returns None instead of raising, so that case must be checked here.
    signer = signers.SimpleSigner.load_pkcs12(pfx_file=str(pfx_path), passphrase=password)
    if signer is None:
        raise ValueError(
            f"No se pudo cargar el certificado PFX ({pfx_path}): "
            "ruta inválida o clave incorrecta"
        )
    return signer


def sign_one_pdf(
    pdf_path: Path,
    out_path: Path,
    cfg: Config,
    stamp_image: Image.Image,
    page_index_0based: int,
    signer: signers.SimpleSigner,
) -> None:
    pdf_image = PdfImage(image=stamp_image)

    stamp_style = stamp.StaticStampStyle(
        background=pdf_image,
        background_layout=layout.SimpleBoxLayoutRule(
            x_align=layout.AxisAlignment.ALIGN_MID,
            y_align=layout.AxisAlignment.ALIGN_MID,
            inner_content_scaling=layout.InnerScaling.STRETCH_FILL,
        ),
        border_width=0,
    )

    box = (
        cfg.pos_x,
        cfg.pos_y,
        cfg.pos_x + cfg.stamp_width,
        cfg.pos_y + cfg.stamp_height,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(pdf_path, "rb") as inf:
        writer = IncrementalPdfFileWriter(inf)

        pdf_signer = signers.PdfSigner(
            signers.PdfSignatureMetadata(
                field_name="Signature",
                subfilter=fields.SigSeedSubFilter.PADES,
                reason=cfg.sign_reason,
                location=cfg.sign_location,
                contact_info=cfg.sign_contact_info,
            ),
            signer=signer,
            stamp_style=stamp_style,
            new_field_spec=fields.SigFieldSpec(
                sig_field_name="Signature",
                on_page=page_index_0based,
                box=box,
            ),
        )

        with open(out_path, "wb") as outf:
            pdf_signer.sign_pdf(writer, output=outf)
