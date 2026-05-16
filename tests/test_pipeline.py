from unittest.mock import MagicMock

from app.rag.pipeline import RAGPipeline


def test_ingest_indexes_chunks(
    pipeline: RAGPipeline,
    fake_embeddings: MagicMock,
    fake_retriever: MagicMock,
) -> None:
    text = "\n\n".join(f"Parágrafo {i} sobre renda fixa." * 3 for i in range(8))
    indexed = pipeline.ingest(text=text, source="renda_fixa.md")

    assert indexed > 0
    assert fake_embeddings.embed.called
    assert fake_retriever.upsert.called
    documents = fake_retriever.upsert.call_args.args[0]
    assert all(d["source"] == "renda_fixa.md" for d in documents)
    assert all("embedding" in d and len(d["embedding"]) == 4 for d in documents)


def test_ingest_empty_text_skips_indexing(
    pipeline: RAGPipeline,
    fake_retriever: MagicMock,
) -> None:
    indexed = pipeline.ingest(text="", source="empty.md")
    assert indexed == 0
    assert not fake_retriever.upsert.called


def test_query_returns_answer_with_citations(
    pipeline: RAGPipeline,
    fake_embeddings: MagicMock,
    fake_generator: MagicMock,
) -> None:
    result = pipeline.query(question="O que é Tesouro Selic?")

    assert "Tesouro Selic" in result.answer
    assert len(result.citations) == 2
    assert result.citations[0].source == "tesouro_direto.md"
    assert result.citations[0].score > 0
    assert fake_embeddings.embed_one.called
    assert fake_generator.generate.called


def test_query_respects_top_k_override(
    pipeline: RAGPipeline,
    fake_retriever: MagicMock,
) -> None:
    pipeline.query(question="qualquer pergunta?", top_k=7)
    args, kwargs = fake_retriever.search.call_args
    assert kwargs.get("top_k") == 7 or (len(args) >= 2 and args[1] == 7)
