# OfflineDocTranslator

OfflineDocTranslator is an offline document translation project focused on deterministic, privacy-preserving document processing.

## Project goals

- Accept PDF, PNG, and JPG/JPEG inputs
- Extract text and document layout locally
- Translate text into selected target languages without internet access during inference
- Reconstruct documents while preserving coordinates, page size, and structure
- Keep OCR, translation, and rendering replaceable through clean interfaces

## Repository layout

- `src/odt/` – package sources
- `tests/` – pytest suite
- `docs/` – project documentation

## Standards

- Python 3.11+
- pytest for tests
- Ruff for linting
- mypy for type checking
- no online translation or OCR services during inference

## Status

This repository is the initial project skeleton. OCR, translation, and rendering implementations are intentionally not included yet.
