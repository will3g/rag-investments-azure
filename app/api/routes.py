from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas import (
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
    SourceModel,
)
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.rag.pipeline import RAGPipeline, build_pipeline

logger = get_logger(__name__)
router = APIRouter()

_pipeline: RAGPipeline | None = None


def get_pipeline(settings: Settings = Depends(get_settings)) -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = build_pipeline(settings)
    return _pipeline


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        provider="azure",
        index=settings.azure_search_index,
    )


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["rag"],
)
def ingest(
    request: IngestRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> IngestResponse:
    try:
        indexed = pipeline.ingest(text=request.text, source=request.source)
    except Exception as exc:
        logger.exception("Falha ao ingerir documento %s", request.source)
        raise HTTPException(status_code=500, detail=f"Erro na ingestão: {exc}") from exc
    return IngestResponse(indexed=indexed, source=request.source)


@router.post("/query", response_model=QueryResponse, tags=["rag"])
def query(
    request: QueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> QueryResponse:
    try:
        result = pipeline.query(question=request.question, top_k=request.top_k)
    except Exception as exc:
        logger.exception("Falha ao processar query")
        raise HTTPException(status_code=500, detail=f"Erro na consulta: {exc}") from exc
    return QueryResponse(
        answer=result.answer,
        sources=[
            SourceModel(
                chunk=c.chunk,
                source=c.source,
                score=c.score,
                position=c.position,
                ingested_at=c.ingested_at,
            )
            for c in result.citations
        ],
    )
