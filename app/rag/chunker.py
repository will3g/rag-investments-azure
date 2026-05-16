from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str
    position: int


class Chunker:
    """Quebra um documento em chunks com overlap.

    Estratégia: RecursiveCharacterTextSplitter com separadores em cascata
    (parágrafo → linha → frase → palavra). Preserva fronteiras semânticas
    sempre que possível e só recorre a corte arbitrário em último caso.
    """

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 120) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap deve ser menor que chunk_size")
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def split(self, text: str, source: str) -> list[Chunk]:
        if not text or not text.strip():
            return []
        pieces = self._splitter.split_text(text)
        return [
            Chunk(text=piece, source=source, position=i)
            for i, piece in enumerate(pieces)
        ]
