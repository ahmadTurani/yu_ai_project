from pdf2image import convert_from_path
import easyocr
import cv2
import numpy as np
from PIL import Image
import requests as rq
import cv2
import numpy as np
import easyocr
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from paddleocr import PaddleOCR
from bidi.algorithm import get_display

EASY_CONF_THRESHOLD = 0.7
def build_paragraph_from_cells(cells, y_threshold=20):
    """
    Convert OCR cells into clean paragraph text.
    """

    # Step 1: group into rows
    rows = []

    for (bbox, text) in cells:
        y = int(bbox[0][1])
        placed = False

        for row in rows:
            if abs(row['y'] - y) < y_threshold:
                row['cells'].append((bbox, text))
                placed = True
                break

        if not placed:
            rows.append({
                "y": y,
                "cells": [(bbox, text)]
            })

    # Step 2: sort rows top → bottom
    rows.sort(key=lambda r: r["y"])

    # Step 3: sort inside each row right → left (Arabic)
    lines = []
    for row in rows:
        row['cells'].sort(key=lambda x: -x[0][0][0])  # sort by x descending
        line = " ".join([cell[1] for cell in row['cells']])
        lines.append(line)

    # Step 4: build paragraph
    paragraph = "\n".join(lines)

    return paragraph 
def process_with_paddle(paddle_engine,cell_crop):
    # PaddleOCR returns a list of [bbox, (text, confidence)]
    result = paddle_engine.ocr(cell_crop, cls=True)
    
    if not result or not result[0]:
        return "", 0
    
    raw_text = result[0][0][1][0]
    confidence = result[0][0][1][1]
    
    # Check if reversal is needed
    # If the text is Arabic, reshape and fix direction
    final_text = get_display(raw_text)
    
    return final_text, confidence

tess_config = r'--oem 3 --psm 6'

POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
# 1. Initialize the Brain (EasyOCR)
# Set gpu=True if you have an NVIDIA graphics card
reader = easyocr.Reader(['ar'], gpu=True)

def improve_cell(crop):
    """ The 'Decision Engine' that fixes the image based on what it sees """
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    
    # Check 1: Is it too dark? (Auto-Brightness)
    avg_brightness = np.mean(gray)
    if avg_brightness < 120:
        # Brighten the image using a simple multiplier
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=30)
    
    # Check 2: Is it low contrast? (Auto-Saturate/Sharpen)
    if gray.std() < 40:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)

    # Check 3: Is it too small? (Auto-Scale)
    h, w = gray.shape
    if h < 40:
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        
    return gray

# 2. Process your PDF
def process_pdf(pdf_path, url):
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH) # 300 DPI is the 'sweet spot'
    chunks = []
    for page_num, page in enumerate(pages):
        all_cells = []
        # Convert PIL image to OpenCV format (NumPy array)
        img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
    
        # 3. FIRST PASS: Find the boxes (detection only)
        # We use detail=1 to get the coordinates of each 'cell'
        cells = reader.readtext(img, add_margin=0.2)
        cells.sort(key=lambda x: (x[0][0][1], -x[0][0][0]))

        print(f"--- Processing Page {page_num + 1} ({len(cells)} cells found) ---")
    
        for (bbox, text, prob) in cells:
            # Extract coordinates [top-left, top-right, bottom-right, bottom-left]
            (tl, tr, br, bl) = bbox
            x_min, y_min = int(tl[0]), int(tl[1])
            x_max, y_max = int(br[0]), int(br[1])
        
            # 4. Crop the specific cell
            cell_crop = img[y_min:y_max, x_min:x_max]
        
            if cell_crop.size == 0: continue # Skip empty crops
        
            # 5. SMART FIX: Apply our adaptive processing
            processed_cell = improve_cell(cell_crop)
        
            # 6. SECOND PASS: Read the fixed cell
            # We pass the processed cell back to EasyOCR
            easyocr_result = reader.readtext(processed_cell, decoder='beamsearch', beamWidth=10)
            easy_text = easyocr_result[0][1] if easyocr_result else ""
            easy_conf = easyocr_result[0][2] if easyocr_result else 0
            paddle_conf = 0
            if easy_conf < 0.7 :
                paddle_engine = PaddleOCR(use_angle_cls=True, lang='ar', show_log=False, use_gpu=True)
                pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
                tess_text = pytesseract.image_to_string(processed_cell, lang='ara+eng', config=tess_config).strip()
                paddle_text, paddle_conf = process_with_paddle(paddle_engine,processed_cell)
            final_output = ""
            # ADD TO YOUR VOTING SYSTEM:
            if paddle_conf > easy_conf:
                final_output = paddle_text
            elif paddle_conf < easy_conf and easy_conf > 0.5:
                final_output = easy_text
            else:
                final_output = tess_text
            if final_output:
                if len(final_output) < 3:
                    continue
                all_cells.append((bbox, final_output))
        page_content = build_paragraph_from_cells(all_cells)

        chunks.append({
            "title": f"Page {page_num + 1}",
            "content": page_content,
            "page_number": page_num + 1,
            "relevant_urls": {},
            "source": url
            })
        print(str(page_num+1) + "/" + str(len(pages)))
        print("Page content preview:", page_content[:200], "...\n")
    return chunks

        