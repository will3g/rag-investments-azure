from typing import Protocol

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings


class EmbeddingsClient(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...


class AzureOpenAIEmbeddings:
    def __init__(self, endpoint: str, api_key: str, api_version: str, deployment: str) -> None:
        self._model = deployment
        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


def build_embeddings_client(settings: Settings) -> EmbeddingsClient:
    if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT e AZURE_OPENAI_API_KEY são obrigatórios")
    return AzureOpenAIEmbeddings(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_embedding_deployment,
    )
