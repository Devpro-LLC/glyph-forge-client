# glyph/core/workspace/engine.py
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

# Public exceptions for engine/adapters
class EngineError(RuntimeError):
    """Generic engine error."""

class EngineConfigError(EngineError):
    """Misconfiguration (missing envs, bad base URL, etc.)."""

class EngineIOError(EngineError):
    """File or network I/O related error."""


@runtime_checkable
class SupportsReadBytes(Protocol):
    """Duck-type protocol for file-like objects that can be read as bytes."""
    def read(self, n: int = -1) -> bytes: ...


def _ensure_file_exists(path: Optional[str], label: str) -> None:
    if path is None:
        return
    if not os.path.exists(path):
        raise EngineIOError(f"{label} not found: {path}")


def _json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


class GlyphEngine:
    """
    Mode-agnostic façade: provides one API no matter where execution happens.
    Adapters (local/client/etc.) implement the real behavior.
    """
    def __init__(self, adapter: "EngineAdapter"):
        self._adapter = adapter

    # -------------------------
    # Stable surface area
    # -------------------------
    def build_schema(
        self,
        *,
        docx_path: Optional[str] = None,
        plaintext_path: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        _ensure_file_exists(docx_path, "DOCX path")
        _ensure_file_exists(plaintext_path, "Plaintext path")
        return self._adapter.build_schema(
            docx_path=docx_path,
            plaintext_path=plaintext_path,
            options=options or {},
        )

    def run_schema(
        self,
        *,
        schema: Dict,
        source_docx: Optional[str] = None,
        plaintext_path: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> List[Any]:
        _ensure_file_exists(source_docx, "Source DOCX path")
        _ensure_file_exists(plaintext_path, "Plaintext path")
        return self._adapter.run_schema(
            schema=schema,
            source_docx=source_docx,
            plaintext_path=plaintext_path,
            options=options or {},
        )

    def intake_plaintext(
        self,
        *,
        plaintext_path: str,
        options: Optional[Dict] = None
    ) -> Dict:
        _ensure_file_exists(plaintext_path, "Plaintext path")
        return self._adapter.intake_plaintext(
            plaintext_path=plaintext_path,
            options=options or {},
        )


class EngineAdapter(ABC):
    """
    Adapter interface. Implementations:
      - LocalEngineAdapter (uses local SDK runners)
      - ClientEngineAdapter (calls FastAPI endpoints)
    """

    @abstractmethod
    def build_schema(
        self,
        *,
        docx_path: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def run_schema(
        self,
        *,
        schema: Dict,
        source_docx: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def intake_plaintext(
        self,
        *,
        plaintext_path: str,
        options: Dict
    ) -> Dict:
        raise NotImplementedError


__all__ = [
    "GlyphEngine",
    "EngineAdapter",
    "EngineError",
    "EngineConfigError",
    "EngineIOError",
]
