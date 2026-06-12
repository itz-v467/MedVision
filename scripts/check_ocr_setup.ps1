# MedVision OCR setup diagnostic
Write-Host "=== MedVision OCR Check ===" -ForegroundColor Cyan

$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:PYTHONPATH = "."

Write-Host "`nPython packages:"
@("pdfplumber", "pypdf", "fitz", "pytesseract", "easyocr", "paddleocr") | ForEach-Object {
    $mod = if ($_ -eq "fitz") { "pymupdf" } else { $_ }
    python -c "import importlib; importlib.import_module('$_'); print('  OK  $_')" 2>$null
    if ($LASTEXITCODE -ne 0) { Write-Host "  MISS $_ (pip install $mod)" -ForegroundColor Yellow }
}

Write-Host "`nTesseract binary:"
$tess = Get-Command tesseract -ErrorAction SilentlyContinue
if ($tess) { Write-Host "  OK  $($tess.Source)" -ForegroundColor Green }
else { Write-Host "  MISS Install from https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Yellow }

Write-Host "`nAPI OCR status (backend must be running on :5000):"
try {
    $r = Invoke-RestMethod -Uri "http://localhost:5000/health/ocr" -TimeoutSec 5
    $r.data | ConvertTo-Json
} catch {
    Write-Host "  Backend not reachable. Start: uvicorn backend.app:create_app --factory --port 5000" -ForegroundColor Yellow
}

Write-Host "`nQuick OCR test (synthetic image):"
python -c @"
import os
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
from PIL import Image, ImageDraw
import tempfile
from pathlib import Path
from backend.client.document_ocr_client import extract_image_text
img = Image.new('RGB', (500, 120), 'white')
ImageDraw.Draw(img).text((10, 30), 'Hemoglobin 12.1 g/dL', fill='black')
p = Path(tempfile.gettempdir()) / 'mv_ocr_test.png'
img.save(p)
t, c, m = extract_image_text(p)
print(f'  method={m} chars={len(t)} text={t[:60]!r}')
"@

Write-Host "`nDone. Re-upload lab report AFTER OCR shows chars > 0." -ForegroundColor Cyan
