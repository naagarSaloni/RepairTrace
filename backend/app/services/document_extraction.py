from pathlib import Path

from pypdf import PdfReader
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_pdf_text(file_path: str | Path) -> str:
    """Extract text from a normal text-based PDF."""

    path = Path(file_path)

    if not path.exists():
        return ""

    try:
        reader = PdfReader(str(path))

        pages = []

        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text)

        return "\n".join(pages).strip()

    except Exception:
        return ""


def extract_image_text(file_path: str | Path) -> str:
    """Extract text from JPG/PNG/WebP using OCR."""

    path = Path(file_path)

    if not path.exists():
        return ""

    try:
        image = Image.open(path)

        text = pytesseract.image_to_string(image)

        return text.strip()

    except Exception:
        return ""


def extract_document_text(file_path: str | Path) -> str:
    """
    Extract actual content from the uploaded document.

    Filename is NOT used for validation.
    """

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(path)

    if extension in {".jpg", ".jpeg", ".png", ".webp"}:
        return extract_image_text(path)

    return ""


def normalize_document_text(text: str | None) -> str:
    """Normalize extracted text for comparison."""

    if not text:
        return ""

    text = text.lower()

    for character in [
        "\n",
        "\r",
        "\t",
        ",",
        ".",
        ":",
        ";",
        "/",
        "\\",
        "-",
        "_",
        "(",
        ")",
        "[",
        "]",
    ]:
        text = text.replace(character, " ")

    return " ".join(text.split())