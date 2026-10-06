from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "tmp" / "pdfs" / "formulas-data.json"
PDF_DIR = ROOT / "output" / "pdf" / "formulacoes_separadas"
RENDER_DIR = ROOT / "tmp" / "pdfs" / "rendered"
RENDER_DIR.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-").lower()[:92]


def category_number(parte: str) -> int:
    match = re.search(r"PARTE\s+(\d+)", parte or "", re.I)
    return int(match.group(1)) if match else 999


def category_title(parte: str) -> str:
    return re.sub(r"^PARTE\s+\d+\s*[—-]\s*", "", parte or "Outros", flags=re.I).strip()


def render_page(pdf_path: Path, page_index: int, scale: float = 1.25) -> Image.Image:
    document = pdfium.PdfDocument(str(pdf_path))
    page = document[page_index]
    image = page.render(scale=scale).to_pil().convert("RGB")
    page.close()
    document.close()
    return image


def contact_sheet(paths: list[Path], page_index: int, output: Path, label: str) -> None:
    columns = 5
    thumb_w, thumb_h = 190, 269
    caption_h = 44
    rows = math.ceil(len(paths) / columns)
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + caption_h)), "#e9edf2")
    draw = ImageDraw.Draw(sheet)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 11) if font_path.exists() else ImageFont.load_default()
    for index, path in enumerate(paths):
        image = render_page(path, min(page_index, len(PdfReader(str(path)).pages) - 1), scale=0.55)
        image.thumbnail((thumb_w - 10, thumb_h - 10))
        x = (index % columns) * thumb_w + (thumb_w - image.width) // 2
        y = (index // columns) * (thumb_h + caption_h) + 5
        sheet.paste(image, (x, y))
        caption = f"{index + 1:02d} · {path.stem[:27]}"
        draw.text(((index % columns) * thumb_w + 8, y + thumb_h), caption, fill="#102957", font=font)
    draw.text((8, 2), label, fill="#102957", font=font)
    sheet.save(output, quality=92)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict]] = {}
    for formula in data.get("formulas") or []:
        grouped.setdefault(formula.get("parte") or "Outros", []).append(formula)

    expected = {}
    for parte, formulas in grouped.items():
        number = category_number(parte)
        title = category_title(parte)
        expected[f"{number:02d}-{slugify(title)}.pdf"] = formulas

    pdf_paths = sorted(PDF_DIR.glob("*.pdf"))
    problems = []
    summaries = []
    if len(pdf_paths) != 30:
        problems.append(f"Esperados 30 PDFs, encontrados {len(pdf_paths)}")

    for path in pdf_paths:
        reader = PdfReader(str(path))
        pages = reader.pages
        formulas = expected.get(path.name)
        if formulas is None:
            problems.append(f"Arquivo inesperado: {path.name}")
            continue
        expected_count = len(formulas)
        extracted = []
        empty_pages = []
        for page_index, page in enumerate(pages):
            text = page.extract_text() or ""
            extracted.append(text)
            if len(text.strip()) < 25:
                empty_pages.append(page_index + 1)
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            if abs(width - 595.276) > 1 or abs(height - 841.89) > 1:
                problems.append(f"Tamanho não A4 em {path.name}, página {page_index + 1}: {width}x{height}")
        all_text = "\n".join(extracted)
        marker_count = len(re.findall(r"FÓRMULA\s+\d+\s+DE\s+\d+", all_text, flags=re.I))
        if marker_count != expected_count:
            problems.append(f"Contagem divergente em {path.name}: {marker_count}/{expected_count}")
        if empty_pages:
            problems.append(f"Páginas vazias em {path.name}: {empty_pages}")
        if "�" in all_text:
            problems.append(f"Caractere corrompido em {path.name}")
        missing_titles = [f.get("titulo") for f in formulas if (f.get("titulo") or "") not in all_text]
        if missing_titles:
            problems.append(f"Títulos ausentes em {path.name}: {len(missing_titles)}")
        summaries.append({
            "file": path.name,
            "formulas": expected_count,
            "pages": len(pages),
            "bytes": path.stat().st_size,
            "empty_pages": empty_pages,
        })

    contact_sheet(pdf_paths, 0, RENDER_DIR / "contact-covers.png", "CAPAS")
    contact_sheet(pdf_paths, 2, RENDER_DIR / "contact-formulas.png", "PRIMEIRAS FÓRMULAS")

    sample = max(pdf_paths, key=lambda p: p.stat().st_size)
    sample_reader = PdfReader(str(sample))
    sample_indexes = [0, 2, len(sample_reader.pages) - 1]
    for label, page_index in zip(("cover", "formula", "last"), sample_indexes):
        render_page(sample, page_index, scale=1.7).save(RENDER_DIR / f"sample-{label}.png")

    report = {
        "pdf_count": len(pdf_paths),
        "formula_count": sum(item["formulas"] for item in summaries),
        "page_count": sum(item["pages"] for item in summaries),
        "problems": problems,
        "files": summaries,
        "sample_pdf": sample.name,
    }
    (ROOT / "tmp" / "pdfs" / "qa-summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "pdf_count": report["pdf_count"],
        "formula_count": report["formula_count"],
        "page_count": report["page_count"],
        "problem_count": len(problems),
        "sample_pdf": sample.name,
    }, ensure_ascii=False))
    if problems:
        for problem in problems[:20]:
            print(f"PROBLEM: {problem}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
