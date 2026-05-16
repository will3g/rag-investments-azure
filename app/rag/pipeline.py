from dataclasses import dataclass

from app.core.config import Settings
from app.core.logging import get_logger
from app.rag.chunker import Chunker
from app.rag.embeddings import EmbeddingsClient, build_embeddings_client
from app.rag.generator import GeneratorClient, build_generator_client
from app.rag.retriever import AzureSearchRetriever

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class Citation:
    source: str
    position: int
    score: float
    chunk: str
    ingested_at: str = ""


@dataclass(frozen=True, slots=True)
class QueryResult:
    answer: str
    citations: list[Citation]


class RAGPipeline:
    def __init__(
        self,
        settings: Settings,
        chunker: Chunker,
        embeddings: EmbeddingsClient,
        retriever: AzureSearchRetriever,
        generator: GeneratorClient,
    ) -> None:
        self._settings = settings
        self._chunker = chunker
        self._embeddings = embeddings
        self._retriever = retriever
        self._generator = generator

    def ensure_index(self) -> None:
        self._retriever.ensure_index()

    def ingest(self, text: str, source: str) -> int:
        chunks = self._chunker.split(text=text, source=source)
        if not chunks:
            logger.warning("Nenhum chunk gerado para %s", source)
            return 0

        vectors = self._embeddings.embed([c.text for c in chunks])
        documents = [
            {
                "content": c.text,
                "source": c.source,
                "position": c.position,
                "embedding": vector,
            }
            for c, vector in zip(chunks, vectors, strict=True)
        ]
        indexed = self._retriever.upsert(documents)
        logger.info("Indexados %d/%d chunks de %s", indexed, len(documents), source)
        return indexed

    def query(self, question: str, top_k: int | None = None) -> QueryResult:
        k = top_k or self._settings.top_k
        question_vector = self._embeddings.embed_one(question)
        chunks = self._retriever.search(query_vector=question_vector, top_k=k)
        answer = self._generator.generate(question=question, chunks=chunks)
        citations = [
            Citation(
                source=c.source,
                position=c.position,
                score=c.score,
                chunk=c.text[:240] + ("..." if len(c.text) > 240 else ""),
                ingested_at=c.ingested_at,
            )
            for c in chunks
        ]
        return QueryResult(answer=answer, citations=citations)


def build_pipeline(settings: Settings) -> RAGPipeline:
    chunker = Chunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    embeddings = build_embeddings_client(settings)
    retriever = AzureSearchRetriever(
        endpoint=settings.azure_search_endpoint,
        api_key=settings.azure_search_key,
        index_name=settings.azure_search_index,
        embedding_dim=settings.embedding_dim,
    )
    generator = build_generator_client(settings)
    return RAGPipeline(
        settings=settings,
        chunker=chunker,
        embeddings=embeddings,
        retriever=retriever,
        generator=generator,
    )
