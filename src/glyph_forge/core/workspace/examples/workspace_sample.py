from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Public API from your redesigned workspace package
from glyph_forge.core.workspace import (
    create_workspace,
    create_engine,
    WorkspaceConfig,
)

# ------------------------------------------------------------------------------
# Choose mode
#   - Local SDK (default): WorkspaceConfig()  OR set GLYPH_MODE=local
#   - Client (FastAPI):    WorkspaceConfig(mode="client", api_base="...", api_key="...")
# ------------------------------------------------------------------------------

USE_CLIENT = False  # flip to True to call your FastAPI instead of local SDK

if USE_CLIENT:
    cfg = WorkspaceConfig(
        mode="client",
        api_base=os.getenv("GLYPH_API_BASE", "https://api.glyphapi.ai"),
        api_key=os.getenv("GLYPH_API_KEY", None),
    )
else:
    cfg = WorkspaceConfig()  # local (no envs required)

# ------------------------------------------------------------------------------
# Inputs (adjust these for your project)
# ------------------------------------------------------------------------------
SAMPLE_DOCX = "samples/input/sample.docx"      # optional: build schema from a DOCX
SAMPLE_TEXT = "samples/input/sample.txt"       # optional: build/intake from plaintext

SCHEMA_NAME = "sample_schema"                  # base name used for saved schema
OUTPUT_DOCX_NAME = "assembled_output.docx"     # where the run will write the DOCX

# ------------------------------------------------------------------------------
# 1) Create a workspace (keeps your tagging system via use_uuid=True)
# ------------------------------------------------------------------------------
ws = create_workspace(use_uuid=True)  # run_id like 20250929T141215_ab12cd34
print(f"[workspace] base_root={ws.base_root}")
print(f"[workspace] run_id={ws.run_id}")
print(f"[workspace] root_dir={ws.root_dir}")

# Useful directories
print("[paths]", ws.paths.as_dict())

# Create an engine bound to this workspace and selected mode
engine = create_engine(ws, cfg)

# ------------------------------------------------------------------------------
# (A) Build a schema from a DOCX (preferred when you have a prototype doc)
#     You can also build from plaintext by passing plaintext_path.
# ------------------------------------------------------------------------------
schema: Dict[str, Any] = engine.build_schema(
    docx_path=SAMPLE_DOCX,        # or None
    plaintext_path=None,          # or SAMPLE_TEXT
    options={
        # <-- put any builder options your implementation supports here -->
        # e.g., "detect_titles": True, "normalize_spacing": True
    },
)
# Save schema JSON into the workspace (output/configs/<SCHEMA_NAME>.json)
schema_path = ws.save_json("output_configs", SCHEMA_NAME, schema)
print(f"[schema] saved → {schema_path}")

# ------------------------------------------------------------------------------
# (B) Intake plaintext (if you’re starting from raw text)
#     This step is optional. It returns a structured analysis your runner can use.
# ------------------------------------------------------------------------------
if Path(SAMPLE_TEXT).exists():
    analysis = engine.intake_plaintext(
        plaintext_path=SAMPLE_TEXT,
        options={
            # e.g., "language": "en", "aggressive_blocking": False
        },
    )
    analysis_path = ws.save_json("output_configs", f"{SCHEMA_NAME}_plaintext_analysis", analysis)
    print(f"[plaintext] analysis saved → {analysis_path}")

# ------------------------------------------------------------------------------
# (C) Run the schema to produce a DOCX
#
# You can:
#   - run with a source DOCX (to preserve/template styling), or
#   - run with plaintext-only (engine will map text into schema style)
#
# Most installs will want to tell the runner to *emit a .docx* into the workspace.
# We pass options that your runner/writer understands (update keys to your code).
# ------------------------------------------------------------------------------
output_docx_path = str(Path(ws.directory("output_docx")) / OUTPUT_DOCX_NAME)

run_result = engine.run_schema(
    schema=schema,
    source_docx=SAMPLE_DOCX,          # or None if pure plaintext drive
    plaintext_path=SAMPLE_TEXT,       # optional; include if using intake/plaintext flow
    options={
        # ↓↓↓ Make sure these match your writer/runner flags ↓↓↓
        "emit_docx": True,
        "emit_options": {
            "dest_path": output_docx_path,
            # Optional: anything your writers support (headers/footers, fonts, etc.)
            # "preserve_styles": True,
            # "track_changes": False,
        },
        # Pass through any execution hints
        # "resolver_mode": "heuristics",
        # "debug": True,
    },
)

# `run_result` is whatever your adapter returns (e.g., list of emittables/blocks, or a summary dict).
# We’ll print a quick summary and point to the generated DOCX location.
print("[run] result type:", type(run_result).__name__)
if isinstance(run_result, dict):
    print(json.dumps({k: run_result[k] for k in list(run_result)[:5]}, indent=2))
elif isinstance(run_result, list):
    print(f"[run] blocks returned: {len(run_result)}")

print(f"[docx] generated → {output_docx_path}")
print("\n✅ done.")
