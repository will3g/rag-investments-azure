import pytest

from app.rag.chunker import Chunk, Chunker


def test_split_empty_text_returns_empty_list() -> None:
    chunker = Chunker()
    assert chunker.split(text="", source="x.md") == []
    assert chunker.split(text="   \n  ", source="x.md") == []


def test_split_short_text_returns_single_chunk() -> None:
    chunker = Chunker(chunk_size=400, chunk_overlap=50)
    result = chunker.split(text="texto curto sobre Tesouro Selic.", source="t.md")
    assert len(result) == 1
    assert result[0].source == "t.md"
    assert result[0].position == 0


def test_split_long_text_produces_multiple_chunks() -> None:
    chunker = Chunker(chunk_size=200, chunk_overlap=40)
    long_text = "\n\n".join(f"Parágrafo {i}: " + ("conteúdo " * 30) for i in range(5))
    result = chunker.split(text=long_text, source="long.md")
    assert len(result) > 1
    assert all(isinstance(c, Chunk) for c in result)
    assert [c.position for c in result] == list(range(len(result)))
    assert all(c.source == "long.md" for c in result)


def test_invalid_overlap_raises() -> None:
    with pytest.raises(ValueError, match="overlap"):
        Chunker(chunk_size=100, chunk_overlap=200)


def test_chunks_respect_max_size() -> None:
    chunker = Chunker(chunk_size=200, chunk_overlap=20)
    text = ("frase. " * 200).strip()
    result = chunker.split(text=text, source="s.md")
    for chunk in result:
        assert len(chunk.text) <= 220  # margem pra separadores
