from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    provider: str
    index: str


class IngestRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Texto a ser indexado")
    source: str = Field(..., min_length=1, description="Identificador da fonte do documento")


class IngestResponse(BaseModel):
    indexed: int = Field(..., description="Quantidade de chunks indexados com sucesso")
    source: str


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, description="Pergunta em linguagem natural")
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceModel(BaseModel):
    chunk: str
    source: str
    score: float
    position: int
    ingested_at: str = ""


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceModel]
