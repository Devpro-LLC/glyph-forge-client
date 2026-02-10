# glyph_forge/core/workspace/adapters/local.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from glyph.core.workspace.runtime.engine import EngineAdapter
from glyph.core.schema_runner.run_schema import GlyphSchemaRunner
from glyph.core.analysis.plaintext.intake import intake_plaintext
from glyph.core.schema.build_schema import GlyphSchemaBuilder
from glyph_forge.core.workspace.storage.base import WorkspaceBase


class LocalEngineAdapter(EngineAdapter):
    """
    Executes everything locally using the SDK's existing modules.
    """

    def __init__(self, workspace: WorkspaceBase):
        self.ws = workspace

    def build_schema(
        self,
        *,
        docx_path: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> Dict:
        from glyph.core.utils.docx_intake import intake_docx

        if not docx_path:
            raise ValueError("docx_path is required for local build_schema")

        intake_result = intake_docx(docx_path, self.ws)

        builder = GlyphSchemaBuilder(
            document_xml_path=str(intake_result.key_files["document_xml"]),
            docx_extract_dir=str(intake_result.unzip_dir),
            source_docx=docx_path,
            tag=getattr(self.ws, "tag", None),
        )
        return builder.run(workspace=self.ws)

    def run_schema(
        self,
        *,
        schema: Dict,
        source_docx: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> List:
        runner = GlyphSchemaRunner(schema)
        return runner.run(**(options or {}))

    def intake_plaintext(
        self,
        *,
        plaintext_path: str,
        options: Dict
    ) -> Dict:
        return intake_plaintext(plaintext_path, **(options or {}))

    def build_glyph(
        self,
        *,
        docx_path: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> Dict:
        from glyph.core.utils.docx_intake import intake_docx
        from glyph.core.build_glyph import GlyphBuilder

        if not docx_path:
            raise ValueError("docx_path is required for local build_glyph")

        intake_result = intake_docx(docx_path, self.ws)
        tag = getattr(self.ws, "tag", None)

        builder = GlyphBuilder(
            document_xml_path=str(intake_result.key_files["document_xml"]),
            docx_extract_dir=str(intake_result.unzip_dir),
            source_docx=docx_path,
            tag=tag,
        )
        result = builder.build(workspace=self.ws)
        result = builder.save(result, workspace=self.ws, tag=tag)

        return result.to_dict()
