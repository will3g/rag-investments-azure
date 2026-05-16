from __future__ import annotations

from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.rag.chunker import Chunker
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import RetrievedChunk


@pytest.fixture
def settings() -> Settings:
    return Settings(
        azure_openai_endpoint="https://fake.openai.azure.com/",
        azure_openai_api_key="fake-openai-key",
        azure_search_endpoint="https://fake.search.windows.net",
        azure_search_key="fake-key",
        azure_search_index="test-index",
        chunk_size=400,
        chunk_overlap=80,
        top_k=3,
        embedding_dim=128,
    )


@pytest.fixture
def fake_embeddings() -> MagicMock:
    client = MagicMock()
    client.embed.side_effect = lambda texts: [[0.1, 0.2, 0.3, 0.4] for _ in texts]
    client.embed_one.return_value = [0.1, 0.2, 0.3, 0.4]
    return client


@pytest.fixture
def fake_retriever() -> MagicMock:
    retriever = MagicMock()
    retriever.upsert.side_effect = lambda docs: len(docs)
    retriever.search.return_value = [
        RetrievedChunk(
            text="Tesouro Selic é pós-fixado e indicado para reserva de emergência.",
            source="tesouro_direto.md",
            position=0,
            score=0.95,
        ),
        RetrievedChunk(
            text="A taxa de custódia da B3 é 0,20% ao ano.",
            source="tesouro_direto.md",
            position=1,
            score=0.87,
        ),
    ]
    retriever.ensure_index.return_value = None
    return retriever


@pytest.fixture
def fake_generator() -> MagicMock:
    generator = MagicMock()
    generator.generate.return_value = (
        "O Tesouro Selic é um título pós-fixado, indicado para reserva de "
        "emergência [#1]. Tem taxa de custódia de 0,20% ao ano [#2]."
    )
    return generator


@pytest.fixture
def pipeline(
    settings: Settings,
    fake_embeddings: MagicMock,
    fake_retriever: MagicMock,
    fake_generator: MagicMock,
) -> RAGPipeline:
    return RAGPipeline(
        settings=settings,
        chunker=Chunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap),
        embeddings=fake_embeddings,
        retriever=fake_retriever,
        generator=fake_generator,
    )


@pytest.fixture
def client(pipeline: RAGPipeline, settings: Settings) -> Iterator[TestClient]:
    from app.api.routes import get_pipeline
    from app.core.config import get_settings
    from app.main import app

    def _override_pipeline() -> RAGPipeline:
        return pipeline

    def _override_settings() -> Settings:
        return settings

    app.dependency_overrides[get_pipeline] = _override_pipeline
    app.dependency_overrides[get_settings] = _override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
