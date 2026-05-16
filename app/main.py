from fastapi import FastAPI

from app.api.routes import router
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    application = FastAPI(
        title="RAG Investimentos",
        description=(
            "API RAG sobre investimentos brasileiros — entrega final FIAP MBA. "
            "Consulte /docs para a especificação OpenAPI."
        ),
        version="0.1.0",
    )
    application.include_router(router)
    return application


app = create_app()
