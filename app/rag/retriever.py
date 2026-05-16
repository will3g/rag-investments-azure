import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery


@dataclass(frozen=True, slots=True)
class RetrievedChunk:
    text: str
    source: str
    position: int
    score: float
    ingested_at: str = ""


class AzureSearchRetriever:
    """Wrapper sobre Azure AI Search para indexação e busca vetorial.

    O índice tem 6 campos:
      - id          (chave do documento)
      - content     (texto do chunk, searchable + retrievable)
      - source      (nome do arquivo de origem, filterable + retrievable)
      - position    (posição do chunk dentro do documento, retrievable)
      - ingested_at (timestamp ISO 8601 da ingestão, filterable + retrievable)
      - embedding   (vetor float, dimensão configurável)
    """

    _ALGO_NAME = "hnsw-config"
    _PROFILE_NAME = "vector-profile"

    def __init__(self, endpoint: str, api_key: str, index_name: str, embedding_dim: int) -> None:
        self._endpoint = endpoint
        self._index_name = index_name
        self._embedding_dim = embedding_dim
        self._credential = AzureKeyCredential(api_key)
        self._index_client = SearchIndexClient(endpoint=endpoint, credential=self._credential)
        self._search_client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=self._credential,
        )

    def ensure_index(self) -> None:
        try:
            self._index_client.get_index(self._index_name)
            return
        except ResourceNotFoundError:
            pass

        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SimpleField(
                name="source",
                type=SearchFieldDataType.String,
                filterable=True,
                facetable=True,
            ),
            SimpleField(name="position", type=SearchFieldDataType.Int32, filterable=True),
            SimpleField(
                name="ingested_at",
                type=SearchFieldDataType.String,
                filterable=True,
            ),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=self._embedding_dim,
                vector_search_profile_name=self._PROFILE_NAME,
            ),
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name=self._ALGO_NAME)],
            profiles=[
                VectorSearchProfile(
                    name=self._PROFILE_NAME,
                    algorithm_configuration_name=self._ALGO_NAME,
                )
            ],
        )

        index = SearchIndex(name=self._index_name, fields=fields, vector_search=vector_search)
        self._index_client.create_index(index)

    def upsert(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0
        now = datetime.now(timezone.utc).isoformat()
        for chunk in chunks:
            chunk.setdefault("id", uuid.uuid4().hex)
            chunk.setdefault("ingested_at", now)
        result = self._search_client.upload_documents(documents=chunks)
        return sum(1 for r in result if r.succeeded)

    def search(self, query_vector: list[float], top_k: int) -> list[RetrievedChunk]:
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
        )
        results = self._search_client.search(
            search_text=None,
            vector_queries=[vector_query],
            select=["content", "source", "position", "ingested_at"],
            top=top_k,
        )
        return [
            RetrievedChunk(
                text=r["content"],
                source=r["source"],
                position=r["position"],
                score=float(r["@search.score"]),
                ingested_at=r.get("ingested_at", ""),
            )
            for r in results
        ]
