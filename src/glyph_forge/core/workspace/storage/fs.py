# glyph/core/workspace/fs.py
from __future__ import annotations
import os, shutil, json, uuid
from datetime import datetime
from typing import Optional, Dict

from .base import WorkspaceBase  # if you split base helpers
# If you haven't made base.py yet, you can keep this file self-contained.

def _default_root_dir() -> str:
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, ".git")):
        return os.path.join(cwd, ".glyph_workspace")
    return os.path.join(cwd, "glyph_workspace")

class FilesystemWorkspace(WorkspaceBase):  # or just `object` if you haven't created base.py yet
    def __init__(self, root_dir: Optional[str] = None, use_uuid: bool = False,
                 custom_paths: Optional[Dict[str, str]] = None):
        if root_dir is None:
            root_dir = _default_root_dir()

        os.makedirs(root_dir, exist_ok=True)
        self.base_root = root_dir

        # run id
        self.run_id = (
            datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
            if use_uuid else "default"
        )

        self.root_dir = os.path.join(self.base_root, self.run_id)
        os.makedirs(self.root_dir, exist_ok=True)

        self.paths = {
            "input_docx":      os.path.join(self.root_dir, "input", "docx"),
            "input_plaintext": os.path.join(self.root_dir, "input", "plaintext"),
            "input_unzipped":  os.path.join(self.root_dir, "input", "unzipped"),
            "output_configs":  os.path.join(self.root_dir, "output", "configs"),
            "output_docx":     os.path.join(self.root_dir, "output", "docx"),
        }
        if custom_paths:
            self.paths.update(custom_paths)

        for path in self.paths.values():
            # Make dirs only (skip files)
            if os.path.splitext(path)[1] == "":
                os.makedirs(path, exist_ok=True)

    # --- helpers (same as your current class) ---
    def save_json(self, key: str, name: str, data: dict) -> str:
        path = os.path.join(self.paths[key], f"{name}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load_json(self, key: str, name: str) -> dict:
        path = os.path.join(self.paths[key], f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_file(self, key: str, src_path: str, dest_name: Optional[str] = None) -> str:
        dest_path = os.path.join(self.paths[key], dest_name or os.path.basename(src_path))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return dest_path

    def directory(self, key: str) -> str:
        return self.paths[key]

    def delete_all(self):
        for path in self.paths.values():
            if os.path.exists(path):
                shutil.rmtree(path)
                os.makedirs(path, exist_ok=True)

    def delete_workspace(self):
        if os.path.exists(self.root_dir):
            shutil.rmtree(self.root_dir)

    def delete_root(self):
        if os.path.exists(self.base_root):
            shutil.rmtree(self.base_root)
