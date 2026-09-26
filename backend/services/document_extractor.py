import shutil
from pathlib import Path
from pypdf import PdfReader
import pytesseract
from PIL import Image

def _configure_tesseract() -> bool:
    """
    Checks if Tesseract is available in PATH or common Windows locations.
    Returns True if ready, False otherwise.
    """
    if shutil.which("tesseract"):
        return True
    
    windows_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(windows_path).exists():
        pytesseract.pytesseract.tesseract_cmd = windows_path
        return True
        
    return False

def extract_text_with_ocr(file_path: str) -> str:
    """
    Renders PDF pages using PyMuPDF and runs Tesseract OCR on the images.
    """
    if not _configure_tesseract():
        print("Warning: Tesseract OCR is not installed or configured. Skipping OCR fallback.")
        return ""

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        ocr_pages = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Render page to image (150 DPI is a good balance of speed/accuracy)
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Run OCR
            text = pytesseract.image_to_string(img)
            if text:
                ocr_pages.append(text)
                
        return "\n".join(ocr_pages).strip()
    except Exception as e:
        print(f"Warning: OCR extraction failed: {e}")
        return ""

def extract_text_from_pdf(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    # 1. Attempt standard extraction
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    extracted_text = "\n".join(pages).strip()

    # 2. Fallback to OCR if text is highly suspicious of being an image-only PDF
    # Threshold: less than 50 characters extracted total
    if len(extracted_text) < 50:
        ocr_text = extract_text_with_ocr(file_path)
        if len(ocr_text) > len(extracted_text):
            return ocr_text

    return extracted_text

def extract_text_from_file(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(file_path)

    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8").strip()

    raise ValueError("Unsupported file type. Use PDF or TXT.")