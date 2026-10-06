from __future__ import annotations

import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
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
COVER_IMAGE = ROOT / "assets" / "images" / "cover-nootropicos-premium.jpg"
OUTPUT_DIR = ROOT / "output" / "pdf" / "amostra-premium"
OUTPUT_PATH = OUTPUT_DIR / "nootropicos-desempenho-cognitivo-premium.pdf"

NAVY = colors.HexColor("#0E2856")
NAVY_2 = colors.HexColor("#173B73")
BLUE = colors.HexColor("#24528F")
TEAL = colors.HexColor("#20B7A4")
TEAL_DARK = colors.HexColor("#0D8D80")
MINT = colors.HexColor("#E4F7F3")
GOLD = colors.HexColor("#E7B94E")
GOLD_DARK = colors.HexColor("#80601D")
GOLD_BG = colors.HexColor("#FFF7E0")
ICE = colors.HexColor("#ECF3FA")
PAPER = colors.HexColor("#F5F7FA")
INK = colors.HexColor("#23385E")
MUTED = colors.HexColor("#61718A")
LINE = colors.HexColor("#D6E0E8")
WHITE = colors.white


def register_fonts() -> None:
    font_dir = Path("C:/Windows/Fonts")
    pdfmetrics.registerFont(TTFont("PremiumRegular", str(font_dir / "arial.ttf")))
    pdfmetrics.registerFont(TTFont("PremiumBold", str(font_dir / "arialbd.ttf")))


def clean_plain(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("—", "-").replace("–", "-").replace("‑", "-")
    text = re.sub(
        "["
        "\U0001F1E6-\U0001FAFF"
        "\u2300-\u23FF"
        "\u2600-\u27BF"
        "\u2B00-\u2BFF"
        "\uFE0E-\uFE0F"
        "\u200D"
        "]+", "", text,
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def safe(value: object) -> str:
    return html.escape(clean_plain(value)).replace("\n", "<br/>")


def labeled_notes(value: object) -> str:
    text = clean_plain(value)
    blocks = [block.strip() for block in re.split(r"\n{2,}", text) if block.strip()]
    formatted = []
    for block in blocks:
        escaped = html.escape(block).replace("\n", "<br/>")
        escaped = re.sub(r"^([^:<]{2,45}:)", r"<b>\1</b>", escaped)
        formatted.append(escaped)
    return "<br/><br/>".join(formatted) or "Não informado."


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CoverKicker", fontName="PremiumBold", fontSize=10, leading=13,
        textColor=colors.HexColor("#7DF0DF"), spaceAfter=7, letterSpacing=1.2,
    ))
    styles.add(ParagraphStyle(
        name="CoverTitlePremium", fontName="PremiumBold", fontSize=29, leading=32,
        textColor=WHITE, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitlePremium", fontName="PremiumRegular", fontSize=11, leading=16,
        textColor=colors.HexColor("#D9E7F4"), spaceAfter=15,
    ))
    styles.add(ParagraphStyle(
        name="CoverChip", fontName="PremiumBold", fontSize=8.5, leading=11,
        textColor=NAVY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="PageTitle", fontName="PremiumBold", fontSize=22, leading=26,
        textColor=NAVY, spaceAfter=9,
    ))
    styles.add(ParagraphStyle(
        name="Lead", fontName="PremiumRegular", fontSize=10.5, leading=16,
        textColor=INK, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="SmallLabel", fontName="PremiumBold", fontSize=7.5, leading=9,
        textColor=TEAL_DARK, letterSpacing=.8,
    ))
    styles.add(ParagraphStyle(
        name="IndexNumber", fontName="PremiumBold", fontSize=10.5, leading=13,
        textColor=TEAL_DARK, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="IndexText", fontName="PremiumRegular", fontSize=8.5, leading=11,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="FormulaCount", fontName="PremiumBold", fontSize=8, leading=10,
        textColor=TEAL_DARK, letterSpacing=.7,
    ))
    styles.add(ParagraphStyle(
        name="FormulaTitlePremium", fontName="PremiumBold", fontSize=17, leading=19.5,
        textColor=NAVY, keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="FormulaNumber", fontName="PremiumBold", fontSize=16, leading=18,
        textColor=WHITE, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="Badge", fontName="PremiumBold", fontSize=7.5, leading=9,
        textColor=TEAL_DARK, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionLabel", fontName="PremiumBold", fontSize=9.5, leading=12,
        textColor=NAVY, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="BodyPremium", fontName="PremiumRegular", fontSize=9.1, leading=13.6,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="EffectText", fontName="PremiumRegular", fontSize=10, leading=15,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="QuickValue", fontName="PremiumBold", fontSize=10.5, leading=13,
        textColor=NAVY, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="QuickLabel", fontName="PremiumBold", fontSize=7.2, leading=9,
        textColor=MUTED, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="TableHeadPremium", fontName="PremiumBold", fontSize=8, leading=10,
        textColor=WHITE,
    ))
    styles.add(ParagraphStyle(
        name="TableCellPremium", fontName="PremiumRegular", fontSize=7.7, leading=9.7,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="DosePremium", fontName="PremiumBold", fontSize=7.7, leading=9.7,
        textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name="BoxTitlePremium", fontName="PremiumBold", fontSize=8.6, leading=10,
        textColor=NAVY, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="BoxBodyPremium", fontName="PremiumRegular", fontSize=7.8, leading=10.6,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="BoxBodyCompact", fontName="PremiumRegular", fontSize=7.1, leading=8.9,
        textColor=INK,
    ))
    styles.add(ParagraphStyle(
        name="Disclaimer", fontName="PremiumRegular", fontSize=7.7, leading=11.5,
        textColor=MUTED,
    ))
    return styles


def draw_cover_background(canvas, doc):
    width, height = A4
    reader = ImageReader(str(COVER_IMAGE))
    image_width, image_height = reader.getSize()
    scale = max(width / image_width, height / image_height)
    draw_width, draw_height = image_width * scale, image_height * scale
    x = (width - draw_width) / 2
    y = (height - draw_height) / 2
    canvas.saveState()
    canvas.drawImage(reader, x, y, draw_width, draw_height, mask="auto")
    canvas.setFillColor(NAVY)
    try:
        canvas.setFillAlpha(.20)
    except Exception:
        pass
    canvas.rect(0, 0, width, height, fill=1, stroke=0)
    try:
        canvas.setFillAlpha(.78)
    except Exception:
        pass
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, width, 118 * mm, fill=1, stroke=0)
    try:
        canvas.setFillAlpha(1)
    except Exception:
        pass
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, 4 * mm, height, fill=1, stroke=0)
    canvas.setFont("PremiumBold", 9)
    canvas.setFillColor(WHITE)
    canvas.drawString(22 * mm, height - 20 * mm, "189 FORMULAÇÕES MAGISTRAIS")
    canvas.setFont("PremiumRegular", 8)
    canvas.setFillColor(colors.HexColor("#C9D8E8"))
    canvas.drawRightString(width - 20 * mm, height - 20 * mm, "COLEÇÃO PREMIUM")
    canvas.restoreState()


def draw_body_page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 15 * mm, width, 15 * mm, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, height - 16.1 * mm, width, 1.1 * mm, fill=1, stroke=0)
    canvas.setFont("PremiumBold", 8.2)
    canvas.setFillColor(WHITE)
    canvas.drawString(18 * mm, height - 9.5 * mm, "NOOTRÓPICOS E DESEMPENHO COGNITIVO")
    canvas.setFont("PremiumRegular", 7.2)
    canvas.setFillColor(colors.HexColor("#C9D8E8"))
    canvas.drawRightString(width - 18 * mm, height - 9.5 * mm, "GUIA DE CONSULTA")
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("PremiumRegular", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9.2 * mm, "Material educativo - avaliação profissional obrigatória.")
    canvas.drawRightString(width - 18 * mm, 9.2 * mm, f"{doc.page:02d}")
    canvas.restoreState()


def cover_chip(text: str, styles, width=45 * mm):
    table = Table([[Paragraph(safe(text), styles["CoverChip"])]], colWidths=[width])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def section_box(title: str, body: object, styles, background, border, formatted=False, compact=False):
    content = [
        Paragraph(safe(title), styles["BoxTitlePremium"]),
        Paragraph(
            labeled_notes(body) if formatted else safe(body) or "Não informado.",
            styles["BoxBodyCompact" if compact else "BoxBodyPremium"],
        ),
    ]
    table = Table([[content]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), background),
        ("BOX", (0, 0), (-1, -1), .75, border),
        ("LINEBEFORE", (0, 0), (0, -1), 3, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def composition_table(items: list[dict], styles):
    rows = [[
        Paragraph("ATIVO", styles["TableHeadPremium"]),
        Paragraph("DOSE DE REFERÊNCIA", styles["TableHeadPremium"]),
    ]]
    for item in items:
        active = item.get("ativo") or item.get("nome") or item.get("substancia") or "-"
        dose = item.get("dose") or "-"
        rows.append([
            Paragraph(safe(active), styles["TableCellPremium"]),
            Paragraph(safe(dose), styles["DosePremium"]),
        ])
    table = Table(rows, colWidths=[126 * mm, 48 * mm], repeatRows=1, hAlign="LEFT")
    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), .45, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for row in range(1, len(rows)):
        commands.append(("BACKGROUND", (0, row), (-1, row), WHITE if row % 2 else PAPER))
    table.setStyle(TableStyle(commands))
    return table


def formula_heading(index: int, total: int, title: str, active_count: int, styles):
    number = Table([[Paragraph(f"{index:02d}", styles["FormulaNumber"])]], colWidths=[15 * mm], rowHeights=[15 * mm])
    number.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0, TEAL),
    ]))
    title_content = [
        Paragraph(f"FÓRMULA {index:02d} DE {total:02d}", styles["FormulaCount"]),
        Paragraph(safe(title), styles["FormulaTitlePremium"]),
    ]
    heading = Table([[number, title_content]], colWidths=[19 * mm, 155 * mm])
    heading.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    badges = [[
        Paragraph("NOOTRÓPICOS", styles["Badge"]),
        Paragraph(f"{active_count} ATIVOS", styles["Badge"]),
        Paragraph("CONSULTA RÁPIDA", styles["Badge"]),
    ]]
    badge_table = Table(badges, colWidths=[54 * mm, 54 * mm, 66 * mm])
    badge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), MINT),
        ("BOX", (0, 0), (-1, -1), .55, colors.HexColor("#B8E6DE")),
        ("INNERGRID", (0, 0), (-1, -1), .55, colors.HexColor("#B8E6DE")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return heading, badge_table


def quick_metrics(formula: dict, styles):
    composition = formula.get("composicao") or []
    posology = clean_plain(formula.get("posologia") or "Não informada")
    if len(posology) > 72:
        posology = posology[:69].rsplit(" ", 1)[0] + "..."
    data = [[
        [Paragraph("ATIVOS", styles["QuickLabel"]), Paragraph(str(len(composition)), styles["QuickValue"])],
        [Paragraph("OBJETIVO", styles["QuickLabel"]), Paragraph(safe(formula.get("objetivo") or "Cognição"), styles["QuickValue"])],
        [Paragraph("USO", styles["QuickLabel"]), Paragraph(safe(posology), styles["QuickValue"])],
    ]]
    table = Table(data, colWidths=[27 * mm, 67 * mm, 80 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WHITE),
        ("BOX", (0, 0), (-1, -1), .6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), .6, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def main() -> None:
    register_fonts()
    styles = build_styles()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    formulas = [
        formula for formula in data.get("formulas") or []
        if "Nootrópicos e Desempenho Cognitivo" in (formula.get("parte") or "")
    ]
    formulas.sort(key=lambda item: int(item.get("id") or 0))
    if len(formulas) != 15:
        raise ValueError(f"Esperadas 15 formulações de nootrópicos, encontradas {len(formulas)}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH), pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=24 * mm, bottomMargin=20 * mm,
        title="Nootrópicos e Desempenho Cognitivo - Edição Premium",
        author="189 Formulações Magistrais",
        subject="Guia premium de formulações magistrais para desempenho cognitivo",
    )

    story = [
        Spacer(1, 111 * mm),
        Paragraph("GUIA PREMIUM · PARTE 05", styles["CoverKicker"]),
        Paragraph("Nootrópicos &<br/>Desempenho Cognitivo", styles["CoverTitlePremium"]),
        Paragraph(
            "15 formulações organizadas para foco, memória, clareza mental e suporte à performance cognitiva.",
            styles["CoverSubtitlePremium"],
        ),
        cover_chip("15 FORMULAÇÕES", styles),
        Spacer(1, 8 * mm),
        Paragraph(
            "Material educativo. Fórmulas, doses e combinações devem ser avaliadas por profissional habilitado.",
            ParagraphStyle(
                "CoverDisclaimer", parent=styles["Disclaimer"], textColor=colors.HexColor("#BFD0E2"),
                fontSize=7.5, leading=10.5,
            ),
        ),
        PageBreak(),
        Paragraph("Sua consulta, muito mais clara", styles["PageTitle"]),
        Paragraph(
            "Esta edição organiza cada fórmula como uma ficha de consulta: primeiro o objetivo e a experiência esperada, depois composição, uso, mecanismo e observações clínicas.",
            styles["Lead"],
        ),
        Spacer(1, 3 * mm),
        section_box(
            "Como ler este guia",
            "1. Identifique o objetivo da fórmula.\n2. Compare os ativos e as doses de referência.\n3. Leia mecanismo, forma farmacêutica, sinergias e contraindicações.\n4. Leve suas dúvidas a um profissional habilitado.",
            styles, MINT, TEAL,
        ),
        Spacer(1, 6 * mm),
        Paragraph("Índice da coleção", styles["PageTitle"]),
    ]

    index_rows = []
    for index, formula in enumerate(formulas, 1):
        index_rows.append([
            Paragraph(f"{index:02d}", styles["IndexNumber"]),
            Paragraph(safe(formula.get("titulo") or "Fórmula sem título"), styles["IndexText"]),
        ])
    index_table = Table(index_rows, colWidths=[14 * mm, 160 * mm])
    index_commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), .4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row in range(len(index_rows)):
        index_commands.append(("BACKGROUND", (0, row), (-1, row), WHITE if row % 2 == 0 else PAPER))
    index_table.setStyle(TableStyle(index_commands))
    story.append(index_table)
    story.extend([
        Spacer(1, 7 * mm),
        section_box(
            "Aviso de responsabilidade",
            "Este conteúdo é exclusivamente informativo e educacional. Não substitui diagnóstico, prescrição, tratamento ou acompanhamento individual. Não utilize substâncias ou fórmulas sem avaliação profissional.",
            styles, GOLD_BG, GOLD,
        ),
    ])

    for index, formula in enumerate(formulas, 1):
        composition = formula.get("composicao") or []
        story.append(PageBreak())
        heading, badges = formula_heading(index, len(formulas), formula.get("titulo") or "Fórmula sem título", len(composition), styles)
        story.extend([heading, Spacer(1, 3 * mm), badges, Spacer(1, 3 * mm)])
        story.append(quick_metrics(formula, styles))
        story.append(Spacer(1, 3 * mm))
        story.append(section_box(
            "O que você vai sentir",
            formula.get("indicacao") or "Não informado.",
            styles, MINT, TEAL,
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Composição e doses de referência", styles["SectionLabel"]))
        story.append(composition_table(composition, styles))
        story.append(Spacer(1, 3 * mm))
        story.append(section_box(
            "Posologia recomendada",
            formula.get("posologia") or "Não informada.",
            styles, GOLD_BG, GOLD,
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(section_box(
            "Mecanismo de ação celular",
            formula.get("mecanismo") or "Não informado.",
            styles, ICE, BLUE, compact=index == 13,
        ))
        story.append(Spacer(1, 3 * mm))
        story.append(section_box(
            "Observações clínicas, sinergias e forma farmacêutica",
            formula.get("observacoes") or "Não informadas.",
            styles, PAPER, LINE, formatted=True, compact=index == 13,
        ))

    doc.build(story, onFirstPage=draw_cover_background, onLaterPages=draw_body_page)
    print(json.dumps({"output": str(OUTPUT_PATH), "formula_count": len(formulas)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
