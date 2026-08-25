# OfflineDocTranslator Architecture

## Overview

The system processes a source document through a deterministic offline pipeline:

Input
→ document detection
→ native PDF extraction OR image rendering
→ OCR
→ layout representation
→ language detection
→ protected-token preprocessing
→ translation
→ layout-aware rendering
→ PDF output

This architecture is intentionally backend-agnostic: OCR, translation, and rendering can be swapped without changing the overall document-processing contract.

## Core rules

- All processing goes through the internal Document model.
- OCR backends must be replaceable.
- Translation backends must be replaceable.
- Rendering must be independent of the translation implementation.
- No network access is allowed during inference.
- Coordinates must remain page-relative.
- Model loading must be explicit.
- Model licenses must be documented.
- Model installation and update actions may use network access, but inference must remain offline.

## Processing pipeline

### 1. Input and document detection

The pipeline accepts supported input types:
- native PDF
- scanned PDF
- PNG
- JPG/JPEG

Responsibilities:
- identify the input type
- validate file structure and integrity
- classify the source as PDF-backed or image-backed
- route the document to the correct extraction path

### 2. Native PDF extraction or image rendering

The system branches depending on the source:
- native PDF: parse text and page structure directly from the PDF object model when available
- scanned PDF or image input: render pages to raster images before OCR and layout analysis

Responsibilities:
- preserve original page size and page ordering
- keep a page-relative coordinate system
- generate a normalized page representation for downstream processing

### 3. OCR backend

The OCR backend converts rendered page images or scanned content into machine-readable text and bounding boxes.

Responsibilities:
- detect text tokens and their bounding boxes
- identify reading order and approximate text blocks
- return OCR results in a normalized, backend-agnostic structure
- remain replaceable through an interface

Constraints:
- must not mutate page geometry
- must preserve coordinates relative to the page
- must expose enough metadata for downstream layout reconstruction

### 4. Layout representation

The layout representation captures the document structure in a backend-neutral form.

Responsibilities:
- represent page size and page index
- store text runs, blocks, tables, images, headers, and footers
- retain bounding boxes and approximate positions
- track reading order and document structure

This stage is the central bridge between OCR extraction and translation.

### 5. Language detection

The language detector determines the source language of each page or textual segment.

Responsibilities:
- detect source language before translation
- support the project’s target languages without internet access
- produce deterministic language metadata needed by the translation stage
- allow backend replacement if better detection is added later

### 6. Protected-token preprocessing

Protected-token preprocessing prevents unsafe or sensitive text from being translated.

Responsibilities:
- detect values that must remain unchanged, such as numbers, units, URLs, email addresses, dates, and engineering identifiers
- annotate tokens and regions as protected
- keep the original text exactly as authored for protected values
- provide a mapping from protected text to its original form

This stage is mandatory before translation and must preserve original document meaning and formatting-sensitive text.

### 7. Translation backend

The translation backend receives eligible text segments and produces target-language text.

Responsibilities:
- translate only non-protected text
- preserve the original segment association and page layout
- accept a target-language identifier
- remain replaceable through a well-defined interface

Constraints:
- must not use cloud APIs during inference
- must not depend on online translation services at runtime
- must not silently rewrite protected or sensitive strings

### 8. Layout-aware rendering

The layout-aware rendering stage rebuilds the translated document while preserving original structure.

Responsibilities:
- operate on the original document geometry and page-relative coordinates
- place translated text at approximately the same location as source content
- preserve images, tables, and page structure as closely as possible
- fit text within the original layout without destroying formatting

This stage must not depend on the translation backend implementation details.

### 9. PDF renderer

The PDF renderer composes the translated document into final output bytes.

Responsibilities:
- produce a new PDF file while preserving page size, images, tables, and approximate positions
- write the final document using the normalized layout representation
- keep output generation independent from translation logic

### 10. Pipeline orchestrator

The pipeline orchestrator coordinates the full process:

Input
→ document detection
→ PDF extraction or image rendering
→ OCR
→ layout representation
→ language detection
→ protected-token preprocessing
→ translation
→ layout-aware rendering
→ PDF output

Responsibilities:
- validate the workflow stage order
- pass the internal Document model between stages
- enforce invariants such as page-relative coordinates and protected-value preservation
- handle explicit model loading and initialization without hidden runtime behavior
- ensure a clean separation between extraction, translation, and rendering

## Internal Document model

The internal Document model is the canonical data structure used across the system.

Responsibilities:
- hold all source document metadata and page information
- store OCR results, layout objects, protected tokens, and translated content
- carry coordinate information in a page-relative coordinate system
- preserve original content and structure throughout processing
- ensure every stage operates on a single, consistent internal representation

The rule is simple: all processing goes through the internal Document model.

## Component responsibilities

### Document model
- represents the canonical internal document state
- stores pages, images, text blocks, tables, and metadata
- tracks page size, coordinate system, and original layout information
- acts as the single source of truth for all processing stages

### PDF reader
- reads native PDF input and extracts pages, metadata, and text where possible
- preserves page geometry and page ordering
- returns page content in a normalized form suitable for the internal Document model
- supports image-backed fallback when native PDF text extraction is insufficient

### OCR backend
- converts image pages to text and layout primitives
- provides text boxes, reading order, and approximate region boundaries
- remains replaceable by different OCR implementations

### Layout detector
- groups OCR output into paragraphs, headings, tables, images, and page structure
- assigns spatial relationships between text regions
- retains page-relative coordinates and structure

### Language detector
- identifies source language or language regions
- provides metadata used for translation decisions
- remains backend-agnostic and explicit about model loading

### Protected-token processor
- identifies values that must not be translated or altered
- protects URLs, dates, emails, numbers, units, and engineering IDs
- ensures exact preservation of sensitive strings

### Translation backend
- translates eligible text segments using an offline backend
- does not alter protected regions
- supports replaceable implementations without changing the orchestration layer

### Text fitting engine
- adjusts translated text to the available space in the original layout
- prevents text overflow while preserving approximate position and structure
- keeps the output visually coherent with the original page design

### PDF renderer
- assembles the translated layout back into a PDF document
- preserves page size, images, tables, and coordinates
- is independent of the translation implementation

### Pipeline orchestrator
- orchestrates document ingestion, OCR, layout detection, translation, and rendering
- validates stage ordering and data invariants
- ensures offline-only inference and explicit model loading

## Explicit model loading and licensing

- Models must be loaded explicitly and never implicitly at inference time.
- The application must never silently fetch or load a model while processing a regular document.
- Licensing information for each model or dependency must be documented before use.
- Model licenses must not be assumed to be compatible with commercial redistribution without explicit verification.

## Non-goals for this phase

This task is architecture-only. It does not implement OCR, translation, or rendering logic.

## Milestones

### Milestone 1: project skeleton and architecture
- define the internal Document model and pipeline contract
- document architecture and responsibilities
- establish offline inference requirements

### Milestone 2: document intake and OCR contract
- implement document detection and format branching
- define OCR backend interfaces and layout data structures

### Milestone 3: translation and protected-token handling
- implement language detection
- implement protected-token preprocessing
- define translation backend interfaces and translation data flow

### Milestone 4: layout-aware rendering and PDF output
- implement the text fitting engine
- implement PDF rendering contract
- verify preserved coordinates and page structure

### Milestone 5: model integration and licensing review
- explicit model loading and credential-free offline inference
- document model licenses and compatibility checks
