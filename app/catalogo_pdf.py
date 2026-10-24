"""Gera o PDF do Ciclo 15 a partir do Markdown versionado."""

from datetime import datetime, timezone
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_PATH = ROOT / "catalogo" / "ciclo-15.md"
PDF_PATH = ROOT / "catalogo" / "ciclo-15.pdf"
FONTE = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")


def gerar(origem: Path = MARKDOWN_PATH, destino: Path = PDF_PATH) -> Path:
    if not FONTE.exists():
        raise FileNotFoundError(f"Fonte Unicode não encontrada em {FONTE}")
    if not origem.exists():
        raise FileNotFoundError(f"Markdown do catálogo não encontrado em {origem}")

    pdf = FPDF()
    pdf.set_creation_date(datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc))
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("DejaVu", "", str(FONTE))
    pdf.add_page()
    pdf.set_font("DejaVu", size=11)

    for linha in origem.read_text(encoding="utf-8").splitlines():
        pdf.set_x(pdf.l_margin)
        if linha.startswith("### "):
            pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("DejaVu", size=13)
            pdf.multi_cell(0, 7, linha.removeprefix("### ").strip())
            pdf.set_font("DejaVu", size=11)
        elif linha.startswith("## "):
            pdf.add_page()
            pdf.set_x(pdf.l_margin)
            pdf.set_font("DejaVu", size=15)
            pdf.multi_cell(0, 8, linha.removeprefix("## ").strip())
            pdf.set_font("DejaVu", size=11)
        elif linha.startswith("# "):
            pdf.set_font("DejaVu", size=18)
            pdf.multi_cell(0, 9, linha.removeprefix("# ").strip())
            pdf.ln(2)
            pdf.set_font("DejaVu", size=11)
        elif linha.startswith("- "):
            pdf.multi_cell(0, 6, "- " + linha.removeprefix("- ").strip())
        elif linha.strip():
            pdf.multi_cell(0, 6, linha.strip())
        else:
            pdf.ln(2)

    destino.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(destino)
    return destino
