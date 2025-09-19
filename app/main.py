import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routers import ai, auth, drafts
from app.routers import article_templates as article_templates_router
from app.routers import epub as epub_router
from app.routers import generation_history as generation_history_router
from app.routers import images as images_router
from app.routers import mcp as mcp_router
from app.routers import migrations as migrations_router
from app.routers import notion as notion_router
from app.routers import obsidian as obsidian_router
from app.routers import templates as templates_router
from app.routers import writing_styles as writing_styles_router
from app.storage import init_storage


def setup_logging() -> None:
    log_dir = Path("log")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # 同じログファイルへのハンドラが既にある場合は追加しない（リロード対策）
    for h in root.handlers:
        if isinstance(h, RotatingFileHandler):
            try:
                if Path(getattr(h, "baseFilename", "")) == log_file:
                    break
            except Exception:
                continue
    else:
        file_h = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_h.setFormatter(fmt)
        root.addHandler(file_h)

    # コンソールにも同じフォーマットを適用（既存があればそのまま）
    has_console = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
        for h in root.handlers
    )
    if not has_console:
        cons = logging.StreamHandler()
        cons.setFormatter(fmt)
        root.addHandler(cons)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "obsidian"):
        logging.getLogger(name).setLevel(logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="Blog Writer API", version="0.1.0")

    # セッションミドルウェアの追加（Google OAuth用）
    import os

    secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")
    app.add_middleware(SessionMiddleware, secret_key=secret_key)

    # CORS: フロントエンド(Next.js)のDevサーバ用
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(drafts.router, prefix="/api/drafts", tags=["drafts"])
    app.include_router(epub_router.router, prefix="/api/epub", tags=["epub"])
    app.include_router(
        obsidian_router.router, prefix="/api/obsidian", tags=["obsidian"]
    )
    app.include_router(
        templates_router.router, prefix="/api/templates", tags=["templates"]
    )
    app.include_router(
        migrations_router.router, prefix="/api/migrate", tags=["migrations"]
    )
    app.include_router(images_router.router, prefix="/api/images", tags=["images"])
    app.include_router(
        article_templates_router.router,
        prefix="/api/article-templates",
        tags=["article-templates"],
    )
    app.include_router(
        generation_history_router.router,
        prefix="/api/generation-history",
        tags=["generation-history"],
    )
    app.include_router(
        notion_router.router,
        prefix="/api/notion",
        tags=["notion"],
    )
    app.include_router(
        mcp_router.router,
        prefix="/api/mcp",
        tags=["mcp"],
    )
    app.include_router(
        writing_styles_router.router,
        prefix="/api/writing-styles",
        tags=["writing-styles"],
    )

    @app.get("/api/health")
    def health() -> Dict[str, str]:
        return {"status": "ok"}

    ai_paths = [
        getattr(r, "path", "")
        for r in app.routes
        if getattr(r, "path", "").startswith("/api/ai")
    ]
    logging.getLogger(__name__).info("mounted.ai.routes=%s", ai_paths)

    return app


setup_logging()
init_storage()
app = create_app()
