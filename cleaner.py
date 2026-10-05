import fitz  # PyMuPDF

MARK_TYPES = {
    fitz.PDF_ANNOT_HIGHLIGHT, fitz.PDF_ANNOT_UNDERLINE, fitz.PDF_ANNOT_STRIKE_OUT,
    fitz.PDF_ANNOT_SQUIGGLY, fitz.PDF_ANNOT_INK, fitz.PDF_ANNOT_SQUARE,
    fitz.PDF_ANNOT_CIRCLE, fitz.PDF_ANNOT_LINE, fitz.PDF_ANNOT_POLYGON,
    fitz.PDF_ANNOT_POLY_LINE, fitz.PDF_ANNOT_FREE_TEXT, fitz.PDF_ANNOT_TEXT,
    fitz.PDF_ANNOT_STAMP, fitz.PDF_ANNOT_CARET, fitz.PDF_ANNOT_FILE_ATTACHMENT,
}


def _is_marker_drawing(d, page_rect):
    """Colored fills (e.g. highlighter strokes flattened into the page) that are not white/page-size."""
    fill = d.get("fill")
    if not fill or d.get("type") not in ("f", "fs"):
        return False
    if all(c > 0.97 for c in fill):  # white background
        return False
    r = d["rect"]
    if r.width >= page_rect.width * 0.95 and r.height >= page_rect.height * 0.95:
        return False  # full page background
    return r.height < 40  # thin bands like a highlighter


def clean_pdf(data: bytes) -> bytes:
    """Remove annotations and highlight-like colored fills; keep text, images and layout."""
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        for page in doc:
            for annot in list(page.annots() or []):
                if annot.type[0] in MARK_TYPES:
                    page.delete_annot(annot)
            marks = [d["rect"] for d in page.get_drawings() if _is_marker_drawing(d, page.rect)]
            if marks:
                for r in marks:
                    page.add_redact_annot(r)
                page.apply_redactions(
                    images=fitz.PDF_REDACT_IMAGE_NONE,
                    graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                    text=fitz.PDF_REDACT_TEXT_NONE,
                )
        return doc.tobytes(garbage=3, deflate=True)
    finally:
        doc.close()
