"""Run API server: python -m api (from repo root with PYTHONPATH=src or pip install -e .)."""

import uvicorn

from api.settings import get_api_settings


def main() -> None:
    settings = get_api_settings()
    uvicorn.run(
        "api.app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
