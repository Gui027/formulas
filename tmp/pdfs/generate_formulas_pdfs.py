from __future__ import annotations

import html
import json
import re
import unicodedata
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "tmp" / "pdfs" / "formulas-data.json"
OUTPUT_DIR = ROOT / "output" / "pdf" / "formulacoes_separadas"

NAVY = colors.HexColor("#102957")
NAVY_LIGHT = colors.HexColor("#1D417C")
TEAL = colors.HexColor("#24AE9F")
TEAL_DARK = colors.HexColor("#168B80")
MINT = colors.HexColor("#EAF8F5")
GOLD = colors.HexColor("#E5B54A")
GOLD_BG = colors.HexColor("#FFF6DD")
INK = colors.HexColor("#26385E")
MUTED = colors.HexColor("#647087")
LINE = colors.HexColor("#DCE4EA")
PAPER = colors.HexColor("#F5F7F9")
WHITE = colors.white


def register_fonts() -> None:
    font_dir = Path("C:/Windows/Fonts")
    regular = font_dir / "arial.ttf"
    bold = font_dir / "arialbd.ttf"
    if regular.exists() and bold.exists():
        pdfmetrics.registerFont(TTFont("GuideRegular", str(regular)))
        pdfmetrics.registerFont(TTFont("GuideBold", str(bold)))
    else:
        raise FileNotFoundError("Fontes Arial não encontradas em C:/Windows/Fonts")


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-").lower()
    return ascii_value[:92] or "categoria"


def category_number(parte: str) -> int:
    match = re.search(r"PARTE\s+(\d+)", parte or "", re.I)
    return int(match.group(1)) if match else 999


def category_title(parte: str) -> str:
    return re.sub(r"^PARTE\s+\d+\s*[—-]\s*", "", parte or "Outros", flags=re.I).strip()


def safe_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(
        "["
        "\U0001F1E6-\U0001FAFF"
        "\u2300-\u23FF"
        "\u2600-\u27BF"
        "\u2B00-\u2BFF"
        "\uFE0E-\uFE0F"
        "\u200D"
        "]+",
        "",
        text,
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text).strip()
    return html.escape(text).replace("\n", "<br/>")


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="BrandLabel", fontName="GuideBold", fontSize=8.5, leading=11,
        textColor=TEAL, spaceAfter=4, uppercase=True,
    ))
    styles.add(ParagraphStyle(
        name="CoverTitle", fontName="GuideBold", fontSize=25, leading=29,
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="CoverPart", fontName="GuideBold", fontSize=10, leading=13,
        textColor=colors.HexColor("#85F0E1"), alignment=TA_CENTER, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle", fontName="GuideRegular", fontSize=10, leading=15,
        textColor=colors.HexColor("#DCE8F6"), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle", fontName="GuideBold", fontSize=18, leading=22,
        textColor=NAVY, spaceBefore=3, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="FormulaNumber", fontName="GuideBold", fontSize=8, leading=10,
        textColor=TEAL_DARK, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="FormulaTitle", fontName="GuideBold", fontSize=18, leading=22,
        textColor=NAVY, spaceAfter=7, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="Objective", fontName="GuideBold", fontSize=8.5, leading=11,
        textColor=TEAL_DARK, backColor=MINT, borderPadding=(5, 8, 5, 8),
        borderRadius=5, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="Subheading", fontName="GuideBold", fontSize=10.5, leading=13,
        textColor=NAVY, spaceBefore=8, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Body", fontName="GuideRegular", fontSize=9.2, leading=14,
        textColor=INK, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="Small", fontName="GuideRegular", fontSize=7.7, leading=11,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="IndexItem", fontName="GuideRegular", fontSize=9.1, leading=13,
        textColor=INK, leftIndent=8, firstLineIndent=-8, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="TableHead", fontName="GuideBold", fontSize=8.5, leading=11,
        textColor=WHITE,
    ))
    styles.add(ParagraphStyle(
        name="TableCell", fontName="GuideRegular", fontSize=8.7, leading=12,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="TableDose", fontName="GuideBold", fontSize=8.7, leading=12,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="BoxTitle", fontName="GuideBold", fontSize=9.4, leading=12,
        textColor=NAVY, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BoxBody", fontName="GuideRegular", fontSize=8.9, leading=13,
        textColor=INK,
    ))
    return styles


def info_box(title: str, body: str, styles, background, border):
    content = [
        Paragraph(safe_text(title), styles["BoxTitle"]),
        Paragraph(safe_text(body) or "Não informado.", styles["BoxBody"]),
    ]
    table = Table([[content]], colWidths=[170 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def composition_table(items: list[dict], styles):
    rows = [[
        Paragraph("ATIVO", styles["TableHead"]),
        Paragraph("DOSE", styles["TableHead"]),
    ]]
    for item in items or []:
        active = item.get("ativo") or item.get("nome") or item.get("substancia") or "-"
        dose = item.get("dose") or "-"
        rows.append([
            Paragraph(safe_text(active), styles["TableCell"]),
            Paragraph(safe_text(dose), styles["TableDose"]),
        ])
    table = Table(rows, colWidths=[130 * mm, 40 * mm], repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_LIGHT),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for row in range(1, len(rows)):
        commands.append(("BACKGROUND", (0, row), (-1, row), WHITE if row % 2 else PAPER))
    table.setStyle(TableStyle(commands))
    return table


def draw_page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
    canvas.setFont("GuideBold", 8.5)
    canvas.setFillColor(WHITE)
    canvas.drawString(20 * mm, height - 8.4 * mm, "FORMULAÇÕES MAGISTRAIS")
    canvas.setFillColor(TEAL)
    canvas.rect(0, height - 14.2 * mm, width, 1.2 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(LINE)
    canvas.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    canvas.setFont("GuideRegular", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(20 * mm, 9.4 * mm, "Material informativo. Consulte um profissional habilitado.")
    canvas.drawRightString(width - 20 * mm, 9.4 * mm, f"Página {doc.page}")
    canvas.restoreState()


def build_pdf(parte: str, formulas: list[dict], styles) -> Path:
    number = category_number(parte)
    title = category_title(parte)
    filename = f"{number:02d}-{slugify(title)}.pdf"
    output_path = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=23 * mm, bottomMargin=20 * mm,
        title=title, author="189 Formulações Magistrais",
        subject=f"Formulações magistrais - {title}",
    )

    story = []
    cover = Table([[
        [
            Paragraph(f"PARTE {number:02d}", styles["CoverPart"]),
            Paragraph(safe_text(title), styles["CoverTitle"]),
            Paragraph(f"{len(formulas)} formulações organizadas por objetivo", styles["CoverSubtitle"]),
        ]
    ]], colWidths=[170 * mm], rowHeights=[96 * mm])
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
        ("BOX", (0, 0), (-1, -1), 2, TEAL),
    ]))
    story.extend([
        Spacer(1, 20 * mm), cover, Spacer(1, 15 * mm),
        Paragraph("GUIA SEPARADO POR OBJETIVO", styles["BrandLabel"]),
        Paragraph(
            "Este arquivo reúne as formulações desta categoria com composição, doses, posologia, mecanismo de ação e observações disponíveis no aplicativo.",
            styles["Body"],
        ),
        Spacer(1, 5 * mm),
        info_box(
            "Aviso importante",
            "Conteúdo exclusivamente informativo e educacional. Não substitui consulta, diagnóstico, prescrição ou acompanhamento individual. Qualquer fórmula, dose ou combinação deve ser avaliada por médico, nutricionista ou farmacêutico habilitado.",
            styles, GOLD_BG, GOLD,
        ),
        PageBreak(),
        Paragraph("Índice de formulações", styles["SectionTitle"]),
    ])

    for index, formula in enumerate(formulas, 1):
        story.append(Paragraph(f"{index:02d}. {safe_text(formula.get('titulo') or 'Fórmula sem título')}", styles["IndexItem"]))

    for index, formula in enumerate(formulas, 1):
        story.append(PageBreak())
        story.append(Paragraph(f"FÓRMULA {index:02d} DE {len(formulas):02d}", styles["FormulaNumber"]))
        story.append(Paragraph(safe_text(formula.get("titulo") or "Fórmula sem título"), styles["FormulaTitle"]))
        objective = formula.get("objetivo") or title
        story.append(Paragraph(f"OBJETIVO: {safe_text(objective)}", styles["Objective"]))

        indication = formula.get("indicacao") or "Não informado."
        story.append(Paragraph("Efeitos no dia a dia", styles["Subheading"]))
        story.append(Paragraph(safe_text(indication), styles["Body"]))

        story.append(Paragraph("Composição", styles["Subheading"]))
        story.append(composition_table(formula.get("composicao") or [], styles))
        story.append(Spacer(1, 4 * mm))

        story.append(info_box(
            "Posologia recomendada",
            formula.get("posologia") or "Não informada.",
            styles, GOLD_BG, GOLD,
        ))
        story.append(Spacer(1, 4 * mm))
        story.append(info_box(
            "Mecanismo de ação celular",
            formula.get("mecanismo") or "Não informado.",
            styles, MINT, TEAL,
        ))
        story.append(Spacer(1, 4 * mm))
        story.append(info_box(
            "Observações clínicas e forma farmacêutica",
            formula.get("observacoes") or "Não informadas.",
            styles, PAPER, LINE,
        ))

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return output_path


def main() -> None:
    register_fonts()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    formulas = data.get("formulas") or []
    grouped: dict[str, list[dict]] = {}
    for formula in formulas:
        grouped.setdefault(formula.get("parte") or "Outros", []).append(formula)

    styles = make_styles()
    outputs = []
    for parte in sorted(grouped, key=category_number):
        category_formulas = sorted(grouped[parte], key=lambda item: int(item.get("id") or 0))
        outputs.append(build_pdf(parte, category_formulas, styles))

    manifest = {
        "pdf_count": len(outputs),
        "formula_count": len(formulas),
        "files": [str(path.resolve()) for path in outputs],
    }
    (ROOT / "tmp" / "pdfs" / "generation-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"pdf_count": len(outputs), "formula_count": len(formulas)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
