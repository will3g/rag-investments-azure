from typing import Protocol

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import Settings
from app.rag.retriever import RetrievedChunk

SYSTEM_PROMPT = """Você é um assistente especializado em investimentos brasileiros.
Responda EXCLUSIVAMENTE com base no CONTEXTO fornecido. Se a resposta não estiver
no contexto, diga claramente: "Não encontrei essa informação na base consultada."

Regras:
- Seja objetivo e didático.
- Cite os trechos do contexto que sustentam sua resposta usando [#índice].
- Não invente dados, valores ou normas que não estejam no contexto.
- Se houver tributação ou regras envolvidas, deixe claro o que está no contexto.
"""


def _build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return f"PERGUNTA: {question}\n\nCONTEXTO: (vazio)"
    blocks = [
        f"[#{i + 1}] (fonte: {c.source})\n{c.text}"
        for i, c in enumerate(chunks)
    ]
    context = "\n\n---\n\n".join(blocks)
    return f"CONTEXTO:\n{context}\n\nPERGUNTA: {question}"


class GeneratorClient(Protocol):
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> str: ...


class AzureOpenAIGenerator:
    def __init__(self, endpoint: str, api_key: str, api_version: str, deployment: str) -> None:
        self._model = deployment
        self._client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def generate(self, question: str, chunks: list[RetrievedChunk]) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(question, chunks)},
            ],
            temperature=0.1,
            max_tokens=600,
        )
        content = response.choices[0].message.content
        return content or ""


def build_generator_client(settings: Settings) -> GeneratorClient:
    if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
        raise RuntimeError("AZURE_OPENAI_ENDPOINT e AZURE_OPENAI_API_KEY são obrigatórios")
    return AzureOpenAIGenerator(
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        deployment=settings.azure_openai_chat_deployment,
    )
