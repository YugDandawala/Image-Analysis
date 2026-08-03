# Universal Image Analysis Pipeline

An enterprise-grade **Compound AI System** that intelligently analyzes any uploaded image — medical scans, UI screenshots, documents, charts, and everyday photographs — through specialized preprocessing modules before generating conversational AI responses.

## Architecture

```
User Upload → Triage Classifier → Specialist Module → Context Assembly → Master VLM → Chat Response
```

| Layer | Engine | Purpose |
|---|---|---|
| Triage | Gemini 3.5 Flash-Lite | Classify image domain |
| Medical | OpenCV CLAHE | Contrast enhancement |
| UI Parser | Gemini Spatial Grounding | Element detection + bounding boxes |
| Document | IBM Docling | OCR + table extraction |
| General | Pass-through | Minimal preprocessing |
| Master VLM | Gemini 3.5 Flash | Final multimodal reasoning |

## Quick Start

### 1. Get a Free API Key

Visit [Google AI Studio](https://aistudio.google.com/) → Create API Key → Copy it.

### 2. Configure Environment

```bash
# Edit .env and paste your API key
GEMINI_API_KEY=your_actual_key_here
```

### 3. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 6. Open the App

Navigate to **http://localhost:5173** in your browser.

## Usage

1. **Upload** an image (drag & drop or click to browse)
2. **Ask** a question about the image
3. **Watch** the pipeline process through each stage
4. **Chat** with follow-up questions (uses cached analysis — no reprocessing)

## Supported Image Types

- 🏥 **Medical**: X-rays, CT scans, MRI, ultrasound
- 💻 **UI Screenshots**: Websites, mobile apps, dashboards
- 📄 **Documents**: PDFs, invoices, receipts, charts, tables
- 📷 **General**: Nature, people, objects, photographs

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: React.js + Vite
- **VLM**: Google Gemini 3.5 Flash (free API)
- **OCR**: IBM Docling
- **Image Processing**: OpenCV + Pillow
- **Orchestration**: LangGraph-inspired pipeline
