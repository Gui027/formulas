from pathlib import Path
import json
import re

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "output" / "pdf" / "amostra-premium" / "nootropicos-desempenho-cognitivo-premium.pdf"
RENDER_DIR = ROOT / "tmp" / "pdfs" / "rendered-premium"
RENDER_DIR.mkdir(parents=True, exist_ok=True)


def render(page_index: int, scale: float = 1.5) -> Image.Image:
    document = pdfium.PdfDocument(str(PDF_PATH))
    page = document[page_index]
    image = page.render(scale=scale).to_pil().convert("RGB")
    page.close()
    document.close()
    return image


reader = PdfReader(str(PDF_PATH))
texts = [(page.extract_text() or "") for page in reader.pages]
joined = "\n".join(texts)
problems = []

marker_count = len(re.findall(r"FÓRMULA\s+\d+\s+DE\s+15", joined, flags=re.I))
if marker_count != 15:
    problems.append(f"Marcadores de fórmula: {marker_count}/15")
if "�" in joined:
    problems.append("Caractere corrompido encontrado")
empty = [index + 1 for index, text in enumerate(texts) if len(text.strip()) < 25]
if empty:
    problems.append(f"Páginas vazias: {empty}")
for index, page in enumerate(reader.pages):
    width, height = float(page.mediabox.width), float(page.mediabox.height)
    if abs(width - 595.276) > 1 or abs(height - 841.89) > 1:
        problems.append(f"Página {index + 1} fora de A4: {width}x{height}")

columns = 4
thumb_w, thumb_h, caption_h = 220, 311, 25
rows = (len(reader.pages) + columns - 1) // columns
sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + caption_h)), "#e7edf3")
draw = ImageDraw.Draw(sheet)
font_path = Path("C:/Windows/Fonts/arial.ttf")
font = ImageFont.truetype(str(font_path), 12) if font_path.exists() else ImageFont.load_default()
for index in range(len(reader.pages)):
    image = render(index, .62)
    image.thumbnail((thumb_w - 10, thumb_h - 10))
    x = (index % columns) * thumb_w + (thumb_w - image.width) // 2
    y = (index // columns) * (thumb_h + caption_h) + 5
    sheet.paste(image, (x, y))
    draw.text((x + 4, y + thumb_h), f"Página {index + 1}", fill="#102957", font=font)
sheet.save(RENDER_DIR / "contact-all-pages.png", quality=92)

sample_indexes = {"cover": 0, "index": 1, "formula": 2, "last": len(reader.pages) - 1}
for name, index in sample_indexes.items():
    render(index, 1.75).save(RENDER_DIR / f"sample-{name}.png")

summary = {
    "pages": len(reader.pages),
    "formulas": marker_count,
    "problems": problems,
    "bytes": PDF_PATH.stat().st_size,
}
(ROOT / "tmp" / "pdfs" / "premium-qa-summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, ensure_ascii=False))
if problems:
    raise SystemExit(1)
