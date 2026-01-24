# Glyph Forge

Local SDK for building and running DOCX schemas. Process documents entirely on your machine - no API key required!

## Installation

```bash
pip install glyph-forge
```

## Quick Start

```python
from glyph_forge import ForgeClient, create_workspace

# Create workspace
ws = create_workspace()

# Initialize client (no API key needed!)
client = ForgeClient()

# Build schema from a template DOCX
schema = client.build_schema_from_docx(
    ws,
    docx_path="template.docx",
    save_as="my_schema"
)

# Run schema with your plaintext
docx_path = client.run_schema(
    ws,
    schema=schema,
    plaintext="Your content here...",
    dest_name="output.docx"
)

print(f"Generated DOCX: {docx_path}")
```

## Features

✅ **No API Key Required** - Works immediately after installation
✅ **100% Local Processing** - All operations run on your machine
✅ **Privacy First** - No data sent to external servers
✅ **Offline Support** - Works without internet connection
✅ **Open Source** - Apache 2.0 licensed, inspect all code
✅ **Fast** - No network latency

## CLI Usage

```bash
# Build schema from template
glyph-forge build template.docx -o ./output

# Build and run in one command
glyph-forge build-and-run template.docx input.txt -o ./output

# Run existing schema
glyph-forge run schema.json input.txt -o ./output
```

## How It Works

Glyph Forge uses the local SDK to:

1. **Extract** - Unzip and parse DOCX XML structure
2. **Analyze** - Detect headings, paragraphs, lists, tables
3. **Build Schema** - Create reusable document templates
4. **Run Schema** - Generate new DOCXs from plaintext

All processing happens locally using `lxml` and `python-docx`.

## Documentation

For more information, visit [glyphapi.ai](https://www.glyphapi.ai/)

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

Copyright 2025 Devpro LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
