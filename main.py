from app.main import app, create_app

# Uvicornが `uv run fastapi dev app/main.py` で見つけるためのエクスポート
# VS Code等のツールからもインポートしやすいようにしておく
__all__ = ["app", "create_app"]
