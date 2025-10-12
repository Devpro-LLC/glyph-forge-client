# Glyph Forge Documentation

This directory contains the Sphinx documentation for Glyph Forge.

## Building Documentation Locally

### Prerequisites

Install documentation dependencies:

```bash
pip install -r ../requirements-dev.txt
```

Or install with optional docs dependencies:

```bash
pip install -e ".[docs]"
```

### Build HTML Documentation

```bash
cd docs_sphinx
make html
```

The built documentation will be in `build/html/`. Open `build/html/index.html` in your browser.

### Clean Build Artifacts

```bash
make clean
```

## Documentation Structure

- `source/` - Documentation source files (RST and Markdown)
  - `conf.py` - Sphinx configuration
  - `index.rst` - Main documentation index
  - `api/` - API reference documentation
  - `user_guide/` - User guides and tutorials
  - `examples/` - Code examples
  - `_static/` - Static assets (CSS, images, etc.)
  - `_templates/` - Custom Sphinx templates

- `build/` - Built documentation (git-ignored)

## Theme

This documentation uses the [Furo](https://pradyunsg.me/furo/) theme, a clean and modern Sphinx theme with excellent mobile support.

## Automatic Deployment

Documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch. The workflow is defined in `.github/workflows/docs.yml`.

View the live documentation at: https://devpro-llc.github.io/glyph-forge-client/

## Writing Documentation

### Adding New Pages

1. Create a new `.rst` or `.md` file in the appropriate directory
2. Add the file to a `toctree` directive in `index.rst` or a relevant parent page
3. Build and test locally
4. Commit and push

### RST vs Markdown

This documentation supports both:
- **reStructuredText (.rst)**: Full Sphinx features, recommended for API docs
- **Markdown (.md)**: Easier syntax via MyST parser, good for guides

## Contributing

See the main project [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.
