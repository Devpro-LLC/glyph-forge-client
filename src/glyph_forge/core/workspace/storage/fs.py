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
        base_root = root_dir

        # run id
        run_id = (
            datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
            if use_uuid else "default"
        )

        root_dir_path = os.path.join(base_root, run_id)
        os.makedirs(root_dir_path, exist_ok=True)

        paths = {
            "input_docx":      os.path.join(root_dir_path, "input", "docx"),
            "input_plaintext": os.path.join(root_dir_path, "input", "plaintext"),
            "input_unzipped":  os.path.join(root_dir_path, "input", "unzipped"),
            "output_configs":  os.path.join(root_dir_path, "output", "configs"),
            "output_docx":     os.path.join(root_dir_path, "output", "docx"),
        }
        if custom_paths:
            paths.update(custom_paths)

        # Initialize parent class with all required parameters
        super().__init__(
            base_root=base_root,
            root_dir=root_dir_path,
            run_id=run_id,
            paths=paths,
        )

        # Create directories
        for path in self._paths.values():
            # Make dirs only (skip files)
            if os.path.splitext(path)[1] == "":
                os.makedirs(path, exist_ok=True)

    # --- helpers (same as your current class) ---
    def save_json(self, key: str, name: str, data: dict) -> str:
        path = os.path.join(self._paths[key], f"{name}.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def load_json(self, key: str, name: str) -> dict:
        path = os.path.join(self._paths[key], f"{name}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_file(self, key: str, src_path: str, dest_name: Optional[str] = None) -> str:
        dest_path = os.path.join(self._paths[key], dest_name or os.path.basename(src_path))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)
        return dest_path

    

    def delete_all(self):
        for path in self._paths.values():
            if os.path.exists(path):
                shutil.rmtree(path)
                os.makedirs(path, exist_ok=True)

    def delete_workspace(self):
        if os.path.exists(self.root_dir):
            shutil.rmtree(self.root_dir)

    def delete_root(self):
        if os.path.exists(self.base_root):
            shutil.rmtree(self.base_root)
