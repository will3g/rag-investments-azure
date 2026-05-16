"""CLI de ingestão.

Lê todos os arquivos `.md` em `data/investimentos/`, divide em chunks, gera
embeddings e indexa no Azure AI Search. Cria o índice se ainda não existir.

Uso:
    python -m scripts.ingest                # diretório padrão (data/investimentos)
    python -m scripts.ingest data/outro     # diretório customizado
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.rag.pipeline import build_pipeline

DEFAULT_DATA_DIR = Path("data/investimentos")
logger = get_logger(__name__)


def main(data_dir: Path) -> int:
    if not data_dir.exists():
        logger.error("Diretório não encontrado: %s", data_dir)
        return 1

    files = sorted(data_dir.rglob("*.md"))
    if not files:
        logger.error("Nenhum arquivo .md em %s", data_dir)
        return 1

    settings = get_settings()
    pipeline = build_pipeline(settings)
    pipeline.ensure_index()

    total = 0
    for file_path in files:
        text = file_path.read_text(encoding="utf-8")
        source = file_path.name
        logger.info("Ingerindo %s (%d bytes)", source, len(text))
        total += pipeline.ingest(text=text, source=source)

    logger.info("Ingestão concluída. Total de chunks indexados: %d", total)
    return 0


if __name__ == "__main__":
    configure_logging()
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_DIR
    sys.exit(main(target))
