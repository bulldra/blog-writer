from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class DirEntry(BaseModel):
    name: str = Field(...)
    path: str = Field(...)
    is_dir: bool = Field(...)


class ListResponse(BaseModel):
    path: str
    parent: str | None
    entries: List[DirEntry]


@router.get("/home")
def get_home_dir() -> dict[str, str]:
    home = str(Path.home())
    return {"home": home}


@router.get("/list")
def list_dir(path: str | None = Query(None)) -> ListResponse:
    base = Path(path or Path.home())
    try:
        base = base.resolve(strict=False)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid path")
    if not base.exists():
        raise HTTPException(status_code=404, detail="path not found")
    if not base.is_dir():
        raise HTTPException(status_code=400, detail="not a directory")

    try:
        entries: list[DirEntry] = []
        for p in base.iterdir():
            # ディレクトリのみ列挙（隠し含む）
            if p.is_dir():
                entries.append(DirEntry(name=p.name, path=str(p), is_dir=True))
        entries.sort(key=lambda e: e.name.lower())
        parent = str(base.parent) if base.parent != base else None
        return ListResponse(path=str(base), parent=parent, entries=entries)
    except PermissionError:
        raise HTTPException(status_code=403, detail="permission denied")
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e))
