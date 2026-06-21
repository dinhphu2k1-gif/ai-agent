"""HTTP API package for Chat SSE backend."""

__all__ = ["app", "create_app"]


def __getattr__(name: str):
    if name in __all__:
        from api.app import app, create_app

        return app if name == "app" else create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
