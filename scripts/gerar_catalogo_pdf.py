"""Gera catalogo/ciclo-15.pdf a partir do Markdown do ciclo."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.catalogo_pdf import gerar

if __name__ == "__main__":
    destino = gerar()
    print(destino)
