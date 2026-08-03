# Universal Image Analysis Pipeline
## System Design & Implementation Specification

---

# 1. Project Overview & Core Philosophy

## Executive Summary

The **Universal Image Analysis Pipeline** is an enterprise-grade **Compound AI System** designed to process, analyse, and enable natural language conversations around **any uploaded image**.

The system supports:

- 🏥 Medical scans
- 💻 Software UI screenshots
- 📄 Documents and PDFs
- 📊 Charts & tables
- 📷 Everyday photographs

Instead of relying on a single Vision Language Model (VLM), the pipeline intelligently routes images through specialised preprocessing modules before passing them to the reasoning model.

This dramatically improves:

- Accuracy
- Reliability
- Hallucination resistance
- OCR quality
- Spatial understanding

---

# 2. The Fundamental Problem

Traditional multimodal models attempt to perform **everything simultaneously**:

- Visual perception
- Object detection
- OCR
- Spatial reasoning
- Language generation

Although this works reasonably well for simple images, it suffers from several serious limitations.

## Problems

### Hallucinations in Dense Information

Examples:

- Misreading tiny text
- Incorrect table values
- Inventing missing UI components
- Wrong numerical interpretation

---

### Lack of Domain Expertise

Generic VLMs struggle with specialised domains such as:

- Medical imaging
- Radiology
- Engineering diagrams
- Scientific charts

Subtle abnormalities are often ignored.

---

### Poor Spatial Understanding

Examples:

- Incorrect button identification
- Wrong coordinate mapping
- Confusing neighbouring UI elements
- Missing layout relationships

---

# 3. Architectural Solution

The project replaces the traditional single-model architecture with a **Compound AI Pipeline** governed by **Dynamic Vision-Agent Routing**.

Instead of asking one model to solve everything, the system:

1. Classifies the image
2. Routes it to specialised processors
3. Extracts deterministic information
4. Combines structured metadata
5. Sends everything to the final reasoning model

This ensures the VLM receives:

- Original image
- Verified OCR output
- UI coordinates
- Enhanced medical image
- Structured metadata

rather than relying entirely on visual inference.

---

# 4. High-Level System Architecture

```text
           User Upload
       (Image + Question)
               │
               ▼
      Layer 1: Triage Dispatcher
               │
      ┌────────┼────────┐
      │        │        │
      ▼        ▼        ▼
 Medical     UI      Document
 Module    Module      Module
      │        │        │
      └────────┼────────┘
               │
               ▼
    Layer 3: Context Assembly
               │
               ▼
 Layer 4: Master Synthesis VLM
               │
               ▼
      Conversational Response
```

---

# 5. Layer-by-Layer System Breakdown

---

## Layer 1 — Ingestion & Triage Dispatcher

### Purpose

Determine the domain of the uploaded image.

### Responsibilities

- Receive image from FastAPI
- Save image into temporary workspace
- Generate thumbnail
- Run lightweight vision classifier
- Return image category

### Output Categories

```text
medical
ui_screenshot
document
general
```

---

## Layer 2 — Specialised Expert Processing Modules

---

### A. Medical Imaging Module

### Focus

- X-rays
- CT Scans
- MRI
- Ultrasound

### Processing Pipeline

```
Image
   │
Grayscale
   │
CLAHE
   │
Enhanced Image
```

### Processing Steps

- Convert to grayscale
- Apply CLAHE
- Improve local contrast
- Highlight subtle structures
- Return enhanced image

### Benefits

- Better fracture visibility
- Improved soft tissue contrast
- Cleaner downstream reasoning

---

### B. UI Screenshot Module

### Focus

- Websites
- Dashboards
- Mobile apps
- Desktop software

### Processing

Uses a specialised UI parser.

Example output:

```json
[
  {
    "type":"button",
    "label":"Login",
    "bbox":[120,450,220,490]
  },
  {
    "type":"textbox",
    "label":"Username",
    "bbox":[80,250,320,290]
  }
]
```

### Benefits

- Precise element detection
- Bounding boxes
- Semantic labels
- Spatial relationships

---

### C. Document & Chart Module

### Focus

- PDFs
- Receipts
- Invoices
- Research papers
- Charts
- Tables

### Processing

OCR extracts:

- Text
- Coordinates
- Tables
- Reading order

Example:

```text
Invoice No: 24567

Date:
12 Jan 2026

Total:
£540
```

### Benefits

- Eliminates OCR hallucinations
- Preserves layout
- Better table reasoning

---

### D. General Image Module

### Focus

- Nature
- People
- Objects
- Animals
- Everyday photographs

### Processing

No heavy preprocessing.

Pipeline:

```
Image
   │
Direct
   │
Context Assembly
```

---

# 6. Layer 3 — Context Assembly Engine

## Purpose

Merge:

- Original image
- OCR results
- UI metadata
- Medical enhancements
- Structured outputs

into a single multimodal prompt.

---

### Prompt Structure

```
IMAGE

+

Structured Metadata

+

System Instructions

+

User Question
```

---

# 7. Layer 4 — Master Synthesis VLM

## Purpose

Provide the final conversational intelligence.

### Responsibilities

- Read injected metadata
- Understand user query
- Perform reasoning
- Generate grounded response
- Maintain chat memory

### Important Feature

Follow-up questions **do not** require rerunning expensive preprocessing unless a new image is uploaded.

---

# 8. Complete Technology Stack

| Layer | Technology | Purpose |
|----------|-----------------------------|------------------------------------------------|
| Backend | FastAPI | Async API handling |
| Workflow | LangGraph | Stateful graph orchestration |
| Frontend | React.js | Interactive UI |
| Classification | GPT-4o-mini / Llama 3.2 Vision | Fast image routing |
| UI Parsing | Microsoft OmniParser v2 | UI understanding |
| OCR | PaddleOCR / EasyOCR | Text extraction |
| Image Processing | OpenCV + Pillow | CLAHE, resizing, preprocessing |
| Reasoning Model | Claude 3.5 Sonnet / Qwen2.5-VL | Final multimodal reasoning |

---

# 9. End-to-End Processing Flow

```text
Upload Image
      │
      ▼
FastAPI Backend
      │
      ▼
Triage Classifier
      │
      ▼
Conditional Routing
      │
 ┌────┼─────┐
 │    │     │
 ▼    ▼     ▼
Medical UI Document
 │    │     │
 └────┼─────┘
      ▼
Context Assembly
      ▼
Master VLM
      ▼
Chat Response
```

---

# 10. Implementation Roadmap

---

## Phase 1 — Foundation

### Objectives

- Create repository structure
- Configure environment variables
- Build FastAPI server
- Accept image uploads
- Receive user prompts

Deliverables:

- Backend API
- Upload endpoint
- Configuration management

---

## Phase 2 — Specialised Processing Pipeline

### Medical Module

Implement:

- Grayscale conversion
- CLAHE enhancement
- Image export

---

### Document Parser

Implement:

- PaddleOCR
- Bounding boxes
- Structured text

---

### UI Parser

Implement:

- OmniParser inference
- Bounding boxes
- Element labels

---

## Phase 3 — LangGraph State Machine

### State Schema

Suggested state object:

```python
{
    "image_path": "",
    "user_prompt": "",
    "category": "",
    "metadata": {},
    "chat_history": [],
    "system_output": ""
}
```

### Graph Nodes

- Upload Node
- Classification Node
- Medical Node
- UI Node
- OCR Node
- Context Assembly Node
- Master VLM Node

### Routing Logic

```
Category

medical
   │
Medical Node

ui
   │
UI Node

document
   │
OCR Node

general
   │
Skip preprocessing
```

---

## Phase 4 — Frontend Development

Build:

- Drag-and-drop upload
- Image preview
- Chat interface
- Upload progress
- Processing status
- Conversation history

Example status:

```text
✔ Routed to UI Parsing Module

✔ OCR Complete

✔ Context Generated

✔ Sending to Master VLM
```

---

## Phase 5 — Testing & Optimisation

### Validation

Test against:

- Noisy medical scans
- Multi-language documents
- Large invoices
- Mobile screenshots
- Corrupted images

---

### Performance Optimisation

- Parallel preprocessing
- Image downscaling
- Cached metadata
- Async execution

---

### Data Safety

Automatically:

- Delete temporary uploads
- Clean execution workspace
- Remove cached artefacts

---

# 11. Advantages

## Absolute Accuracy

Specialised tools provide deterministic information rather than forcing the reasoning model to guess.

---

## Extensibility

New processing modules can easily be added.

Examples:

- Satellite imagery
- Industrial inspection
- Circuit diagrams
- Architectural blueprints
- Chemical structures

---

## Resource Efficiency

The reasoning model receives clean, structured data instead of raw pixels alone.

Benefits:

- Lower token usage
- Reduced compute
- Faster responses
- Better reasoning quality

---

# 12. Future Expansion

Potential future modules include:

- 🌍 Satellite Image Analysis
- 🏭 Industrial Defect Detection
- 🧬 Histopathology Analysis
- 🗺️ GIS Map Understanding
- 🏗️ CAD Drawing Analysis
- 🧪 Scientific Figure Interpretation
- 🎥 Video Frame Analysis
- 📈 Financial Chart Intelligence

---

# 13. Summary

The Universal Image Analysis Pipeline introduces a modular, graph-driven architecture that separates **visual perception** from **language reasoning**.

By routing images through specialised preprocessing modules before invoking a powerful Vision Language Model, the system achieves:

- Higher accuracy
- Reduced hallucinations
- Better OCR performance
- Improved UI understanding
- Stronger medical image interpretation
- Lower computational cost
- Easy extensibility for future domains

This compound AI architecture provides a scalable foundation for enterprise-grade image understanding across a wide variety of real-world applications.