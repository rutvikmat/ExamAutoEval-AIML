# evaluator/hwr_service.py

import pytesseract
from PIL import Image
import os
from django.conf import settings

# NOTE: Set the path to your Tesseract executable if not in system PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' 

def recognize_handwriting(image_name):
    """
    Extracts text from a saved image file using Tesseract OCR (Placeholder for custom CRNN).
    """
    try:
        image_path = os.path.join(settings.MEDIA_ROOT, image_name)
        img = Image.open(image_path)
        
        # Using Tesseract for OCR 
        text = pytesseract.image_to_string(img, lang='eng', config='--psm 6')
        
        return text.strip()
        
    except pytesseract.TesseractNotFoundError:
        return "ERROR: Tesseract not found. Please install Tesseract OCR or set the path."
    except Exception as e:
        return f"ERROR during HWR: {e}"