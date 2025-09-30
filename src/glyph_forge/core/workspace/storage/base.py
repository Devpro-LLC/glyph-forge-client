# glyph/core/workspace/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Mapping, Literal, Optional, TypedDict, cast

# ---- Typed keys for path registry -------------------------------------------------

PathKey = Literal[
    "input_docx",
    "input_plaintext",
    "input_unzipped",
    "output_configs",
    "output_docx",
]

PATH_KEYS: tuple[PathKey, ...] = (
    "input_docx",
    "input_plaintext",
    "input_unzipped",
    "output_configs",
    "output_docx",
)

class PathMap(TypedDict):
    input_docx: str
    input_plaintext: str
    input_unzipped: str
    output_configs: str
    output_docx: str

@dataclass(frozen=True)
class PathRegistry:
    """Strongly-typed container for workspace directories."""
    input_docx: str
    input_plaintext: str
    input_unzipped: str
    output_configs: str
    output_docx: str

    def as_dict(self) -> PathMap:
        return cast(PathMap, {
            "input_docx": self.input_docx,
            "input_plaintext": self.input_plaintext,
            "input_unzipped": self.input_unzipped,
            "output_configs": self.output_configs,
            "output_docx": self.output_docx,
        })

# ---- Base class: stores identity + validated paths; leaves I/O to concrete impls --

class WorkspaceBase(ABC):
    """
    Abstract base for glyph workspaces.

    Responsibilities (base):
      - Keep identity (base_root, root_dir, run_id)
      - Validate and expose a typed path registry
      - Provide common helpers that do NOT touch the filesystem

    Responsibilities (concrete subclass, e.g., FilesystemWorkspace in fs.py):
      - Create directories
      - Implement save/load/delete behaviors with real I/O
    """

    def __init__(
        self,
        *,
        base_root: str,
        root_dir: str,
        run_id: str,
        paths: Mapping[str, str],
    ) -> None:
        self.base_root = base_root
        self.root_dir = root_dir
        self.run_id = run_id
        self._paths = self._validate_and_freeze_paths(paths)

    # ---- path registry ------------------------------------------------------------

    @property
    def paths(self) -> PathRegistry:
        """Typed view over the internal path mapping."""
        pm = cast(PathMap, {
            "input_docx": self._paths["input_docx"],
            "input_plaintext": self._paths["input_plaintext"],
            "input_unzipped": self._paths["input_unzipped"],
            "output_configs": self._paths["output_configs"],
            "output_docx": self._paths["output_docx"],
        })
        return PathRegistry(**pm)

    def directory(self, key: PathKey) -> str:
        """Return the directory path for a given storage key."""
        return self._paths[key]

    # ---- abstract I/O API ---------------------------------------------------------

    @abstractmethod
    def save_json(self, key: PathKey, name: str, data: dict) -> str:
        """Persist JSON to the directory mapped by `key`. Return full file path."""
        raise NotImplementedError

    @abstractmethod
    def load_json(self, key: PathKey, name: str) -> dict:
        """Load JSON from the directory mapped by `key`."""
        raise NotImplementedError

    @abstractmethod
    def save_file(self, key: PathKey, src_path: str, dest_name: Optional[str] = None) -> str:
        """
        Copy/stream a file into the directory mapped by `key`.
        Return the destination path.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_all(self) -> None:
        """Delete contents of all registered directories (keep the directories)."""
        raise NotImplementedError

    @abstractmethod
    def delete_workspace(self) -> None:
        """Delete the entire current run folder (self.root_dir)."""
        raise NotImplementedError

    @abstractmethod
    def delete_root(self) -> None:
        """Delete the entire workspace root (all runs). Use with caution."""
        raise NotImplementedError

    # ---- helpers -----------------------------------------------------------------

    @staticmethod
    def _validate_and_freeze_paths(paths: Mapping[str, str]) -> Dict[PathKey, str]:
        missing = [k for k in PATH_KEYS if k not in paths]
        extra = [k for k in paths.keys() if k not in PATH_KEYS]
        if missing:
            raise ValueError(f"Path mapping missing required keys: {missing}")
        if extra:
            # Allow future extension if you want; for now, be strict:
            raise ValueError(f"Path mapping has unsupported keys: {extra}")
        # Freeze into a plain dict[PathKey, str] for fast lookup
        return {cast(PathKey, k): str(paths[k]) for k in PATH_KEYS}
