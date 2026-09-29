<div align="center">

# BIScope

### AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers

**Smart India Hackathon 2026 · Problem Statement SIH26107 · Team HexaDice**

![Category](https://img.shields.io/badge/Category-Software-blue)
![Theme](https://img.shields.io/badge/Theme-Smart%20Automation-blue)
![Backend Tests](https://img.shields.io/badge/backend%20tests-64%2F64%20passed-brightgreen)
![Products](https://img.shields.io/badge/supported%20products-18-informational)
![Requirements](https://img.shields.io/badge/detailed%20requirements-117-informational)

</div>

---

> **Important:** BIScope is an information and review aid. It does **not** certify products, determine legal compliance, guarantee BIS certification, or perform laboratory testing. Every standard it surfaces is a **candidate standard**. Final applicability and compliance must be verified against official BIS sources.

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [How BIScope Works](#how-biscope-works)
4. [Current MVP Features](#current-mvp-features)
5. [Source of Truth vs. AI Layer](#source-of-truth-vs-ai-layer)
6. [Architecture](#architecture)
7. [Technology Stack](#technology-stack)
8. [Supported Products](#supported-products)
9. [Project Structure](#project-structure)
10. [Getting Started](#getting-started)
11. [API Reference](#api-reference)
12. [Database](#database)
13. [Testing](#testing)
14. [Security and Robustness Fixes](#security-and-robustness-fixes)
15. [Safety and Verification Notes](#safety-and-verification-notes)
16. [Current Limitations](#current-limitations)
17. [Future Enhancements](#future-enhancements)
18. [SIH 2026 Information](#sih-2026-information)
19. [Repository](#repository)

---

## Overview

BIScope helps industries and consumers understand product-related BIS information by connecting everyday product terminology to candidate Indian Standards, detailed requirements, supporting evidence, and source-grounded explanations.

Instead of expecting users to already know the formal BIS terminology or the relevant standard number, BIScope offers a guided workflow from a plain-language product description to a candidate standard, its requirements, and an evidence review, with an AI assistant to explain what is already in the system.

---

## Problem Statement

Users often know their product in everyday language but may not know:

- The formal BIS terminology
- Which Indian Standard is relevant
- What the standard covers
- Which version or revision is associated with it
- What requirements need to be reviewed
- What evidence or documents relate to those requirements
- Where the authoritative BIS source can be checked

BIScope provides a guided workflow to address these gaps.

---

## How BIScope Works

The core flow is **Understand → Find → Explain → Review → Next Step**.

The user journey in the interface is:

```text
Product / query → Candidate Standard → Explanation → Requirements → Evidence → AI Assistant
```

---

## Current MVP Features

The following capabilities are implemented in the current MVP.

### BIS Terminology Bridge

Converts everyday user terminology into terminology understood by the BIScope dataset. Supported behaviour:

- Synonyms and alternate product terms
- Text normalization
- Common spelling variations
- Typo recovery
- Ambiguous-term detection
- Unsupported-term handling
- Confidence-based matching

BIScope is designed **not** to invent a standard when a reliable supported match is unavailable.

### Smart Search Recovery

The search layer handles different capitalization, extra spaces, common spelling mistakes, everyday terminology, and supported synonyms. Word/phrase matching also prevents false matches such as treating *cement* as a match for *reinforcement steel bars*, while preserving valid product-code matching.

### Candidate Standard Discovery

After a supported product is identified, BIScope retrieves its associated candidate standard. Depending on availability, the interface can show:

- Standard number, title, edition/year, and status
- Scope
- Revision information and newer-edition information
- Amendment information
- QCO/certification context
- Official source link

The wording **candidate standard** is used deliberately. BIScope does not state that a standard is definitively the applicable one.

### Why This Standard?

Explains why a candidate standard is associated with the selected product, using structured information such as product category, product characteristics, material, intended use, terminology match, and standard scope. The explanation is based on the information available in BIScope.

### Why Not Alternatives?

Identifies alternative candidate information and explains mismatches between the selected product/context and those alternatives. This is informational guidance, not a legal or certification decision.

### Standard / Version Details

Structured metadata for standards, where available: standard number, edition/year, revision, newer-edition information, current status, scope, amendment information, QCO information, official source, and verification notes. Information that could not be verified is intentionally left unverified rather than invented.

### Requirement Explorer

Detailed requirements for the supported products. Each requirement can include a requirement ID, name, description, clause/reference, conditions, evidence information, verification status, notes, and source information.

Example, **Packaged Drinking Water (IS 14543:2024)** has 7 detailed requirements:

1. General product requirements
2. Microbiological requirements
3. Chemical requirements
4. Pesticide residue requirements
5. Radioactive substance requirements
6. Packaging and container requirements
7. Marking and labelling requirements

### Requirement → Evidence Mapping

Users can upload supported evidence documents. BIScope extracts information from the document and compares it against the available requirement information. Each requirement is classified as:

- **Matched**
- **Partially matched**
- **Requires review / missing information**

Demo example with a Packaged Drinking Water evidence document:

| Requirement | Result |
|---|---|
| REQ001 | Matched |
| REQ006 | Matched |
| REQ007 | Matched |
| REQ002 – REQ005 | Partially matched |

> **Evidence matching is not** BIS certification, legal compliance, laboratory verification, or guaranteed conformity. It is an evidence-review aid.

### Conversational AI Assistant

A conversational layer using the Groq API helps users understand information already available within BIScope: products, candidate standards, requirements, terminology, evidence, BIScope functionality, and standard relationships.

### AI Timeout Fallback

If the Groq request times out, BIScope returns a data-grounded fallback response instead of failing.

### Official BIS Source References

Where official BIS source URLs could be verified, they are included in the structured dataset (BIS LIMS).

`IS 14543:2024` · `IS 2925:1984` · `IS 4246:2025` · `IS 694:2010` · `IS 16240:2023` · `IS 15658:2021` · `IS 9873` · `IS 996` · `IS 374:2019` · `IS 2052:2023` · `IS 1180 Part 1` · `IS 1786:2008` · `IS 269:2015` · `IS 13252 Part 1:2010`

For standards where an official source URL could not be confidently verified, the source is left unpopulated rather than guessed.

---

## Source of Truth vs. AI Layer

This separation is the central design principle of BIScope.

| Layer | Role |
|---|---|
| **Structured BIScope data** (products, standards, requirements, terminology, evidence mappings) | **Source of truth** |
| **AI / Groq** | **Explanation and conversation layer only** |

The AI layer does not replace the structured data and is not supposed to invent:

- Standards
- Requirements
- Clauses
- Certification results
- Compliance verdicts

AI responses are explanatory, not authoritative.

---

## Architecture

The architecture is intentionally simple:

```text
User
  ↓
React + TypeScript frontend
  ↓
FastAPI REST API
  ├── Structured BIScope data (source of truth)
  │     └── SQLite / JSON
  └── AI / Groq explanation layer
        └── Data-grounded response with timeout fallback
```

---

## Technology Stack

| Area | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, HTML, CSS |
| Backend | Python, FastAPI, Uvicorn |
| Database | SQLite, JSON / structured project data |
| AI layer | Groq API |
| Testing | Python `unittest`-style backend test suite (64 tests) |

Major backend areas: terminology, search, standards, requirements, evidence, AI chat, and database access.

---

## Supported Products

The current dataset contains **18 supported product records** and **117 detailed requirement records**.

| | | |
|---|---|---|
| Packaged Drinking Water | Sandals and Slippers | Industrial Safety Helmet |
| LPG Gas Stove | PVC Insulated Cable | RO Water Treatment System |
| Storage Water Heater | Paver Blocks | Toys |
| LPG/CNG Valves | Single-Phase Induction Motor | Electric Ceiling Fan |
| Cattle Feed | Distribution Transformer | Reinforcement Steel Bars |
| Cement | Solar Water Pump | IT Equipment |

---

## Project Structure

```text
BIScope/
├── README.md
├── LICENSE
├── .gitignore
├── backend/
│   ├── main.py                       # FastAPI app, CORS, /health, router registration
│   ├── requirements.txt
│   ├── .env.example                  # Groq configuration template
│   ├── api/
│   │   ├── routes.py                 # REST endpoints
│   │   └── schemas.py                # Pydantic request/response models
│   ├── services/
│   │   ├── terminology.py            # Terminology Bridge
│   │   ├── standard_search.py        # Search, standard details, explanations, alternatives
│   │   ├── bis_data.py               # Database-backed product/standard lookup
│   │   ├── requirements.py           # Requirement summaries
│   │   ├── detailed_requirements.py  # Detailed requirements
│   │   ├── document_extractor.py     # Text extraction from uploaded documents
│   │   ├── evidence_mapping.py       # Requirement → evidence mapping
│   │   └── ai_chat.py                # Groq conversational layer + timeout fallback
│   ├── data/
│   │   ├── standards_data.py
│   │   ├── terminology_data.py
│   │   ├── requirements_data.py
│   │   ├── detailed_requirements.py
│   │   └── detailed_requirements.json
│   └── tests/                        # Backend test suite
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── types.ts
│       └── lib/api.ts                # API client
└── scripts/
    └── import_data.py                # SQLite schema creation and data import
```

---

## Getting Started

### Prerequisites

- Python 3
- Node.js and npm
- A Groq API key, needed only for the conversational AI layer

### 1. Clone the repository

```bash
git clone https://github.com/sruthika-19/BIScope.git
cd BIScope
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env            # Windows: copy .env.example .env
```

Edit `backend/.env` and set your Groq API key:

```env
GROQ_API_KEY="your_groq_api_key_here"
```

`.env.example` also contains a `GROQ_MODEL` variable that selects the Groq model. Do not commit `.env`; it is listed in `.gitignore`.

Start the API server:

```bash
python -m uvicorn main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`, with interactive FastAPI docs at `http://localhost:8000/docs`.

The SQLite database does not need to be created manually. If it is missing, the backend initializes it from the project's structured data (see [Database](#database)).

### 3. Frontend setup

In a second terminal:

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

The frontend runs at `http://localhost:5173`. It calls the backend at `http://localhost:8000` by default; set `VITE_API_BASE` to point it elsewhere.

> The backend currently allows CORS only for `http://localhost:5173`, so run the frontend on that origin for the local setup.

Other frontend scripts:

```bash
npm.cmd run build     # Type-check and production build
npm.cmd run lint      # Lint with oxlint
npm.cmd run preview   # Preview the production build
```

---

## API Reference

All endpoints below are registered under the `/api/v1` prefix, except `/health`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/api/v1/terminology/analyze` | Analyze a user query through the Terminology Bridge |
| `GET` | `/api/v1/search?query=...` | Search supported products/standards |
| `GET` | `/api/v1/standards/{standard_id}` | Standard / version details |
| `GET` | `/api/v1/standards/{standard_id}/explanation?product_id=...` | "Why this standard?" explanation |
| `GET` | `/api/v1/standards/{standard_id}/alternatives?product_id=...` | "Why not alternatives?" explanation |
| `GET` | `/api/v1/requirements` | Requirement summaries for all supported products |
| `GET` | `/api/v1/requirements/{product_id}` | Requirement summary for one product |
| `GET` | `/api/v1/requirements/{product_id}/detailed` | Detailed requirements for one product |
| `POST` | `/api/v1/evidence/analyze` | Map submitted document text to requirements (`product_id` and `document_text` parameters) |
| `POST` | `/api/v1/evidence/upload` | Upload a PDF or TXT evidence document (multipart form: `product_id`, `file`) and map it to requirements |
| `POST` | `/api/v1/chat` | Conversational AI assistant (`message`, `conversation_history`) |

Notes:

- `product_id` is a product code such as `P001`.
- `standard_id` is validated to be a positive integer within a safe range before any database access.
- Evidence upload accepts `.pdf` and `.txt` files only. Documents without readable text (for example, scanned image-only files) are rejected; OCR is not currently supported.

---

## Database

BIScope uses SQLite with automatic initialization.

- The database file is created at `backend/database/biscope.db`.
- `.db` files are git-ignored, so the database is not stored in the repository.
- When the database is missing, the backend initializes it from the project's structured data using `scripts/import_data.py`.
- The importer creates and populates three tables: **products**, **standards**, and **product-standard mappings**.
- Database field mapping was corrected so the importer uses `product_name`, `standard_number`, and `edition_year` rather than deriving incorrect values from product codes.

---

## Testing

The backend test suite has **64 tests, and all 64 pass**.

```bash
cd backend
python -m unittest discover -s tests -t .
```

Expected result:

```text
Ran 64 tests
OK
```

Coverage areas:

- API behavior
- AI chat behavior
- Database-backed lookup
- Requirements and detailed requirements
- Evidence mapping
- Terminology
- Search
- Real-world scenarios
- Security and upload handling
- Standard ID validation
- Regression cases

---

## Security and Robustness Fixes

| Issue | Fix |
|---|---|
| **Upload path traversal**: an uploaded filename could contain path components | Only the filename itself is used; path components are stripped |
| **Duplicate upload filenames**: two uploads with the same name could overwrite each other | A unique server-side filename is generated; the original filename is preserved in the response |
| **Oversized `standard_id`**: an extremely large value could cause an SQLite/Python integer overflow and an HTTP 500 | The API validates the standard ID range before database access |
| **CORS**: wildcard configuration | Restricted to `http://localhost:5173` for the current local frontend setup |

---

## Safety and Verification Notes

BIScope is built to avoid overstating what it knows:

- Standards are presented as **candidate standards**, never as a definitive applicability decision.
- Structured BIScope data is the source of truth; AI output is explanatory only.
- Information that could not be verified is left unverified rather than guessed, including official source URLs.
- Evidence matching is a review aid. It is not certification, legal compliance, laboratory verification, or a guarantee of conformity.
- BIScope does not claim complete BIS coverage, live BIS synchronization, or automatic verification of every current BIS regulation.

BIScope helps users discover and review candidate standards, requirements, and supporting evidence using structured, source-grounded information. **Final applicability and compliance must be verified against official BIS sources.**

---

## Current Limitations

- The dataset is limited to 18 supported products and does not represent the entire BIS ecosystem.
- Some source metadata still requires verification.
- Evidence analysis is limited to the available document content and the implemented matching logic.
- AI responses are explanatory rather than authoritative.
- Formal certification and compliance decisions remain outside BIScope.
- Complete live synchronization with BIS sources is not currently claimed.

---

## Future Enhancements

The following are **planned and not yet implemented**:

- Expanded BIS product and standard coverage
- Verified synchronization / update monitoring with official BIS sources, where feasible
- Improved multilingual assistance
- Expanded terminology coverage
- Advanced document extraction
- Clause-level evidence mapping
- Better amendment and version tracking
- Expanded BIS service workflows
- More detailed source traceability
- Voice and accessibility improvements

---

## SIH 2026 Information

| | |
|---|---|
| **Hackathon** | Smart India Hackathon 2026 |
| **Problem Statement ID** | SIH26107 |
| **Problem Statement** | AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers |
| **Theme** | Smart Automation |
| **Category** | Software |
| **Team Name** | HexaDice |
| **Team ID** | 151458 |

---

## Repository

**GitHub:** [https://github.com/sruthika-19/BIScope](https://github.com/sruthika-19/BIScope)

---

<div align="center">

**BIScope** · Team HexaDice · Smart India Hackathon 2026

*Candidate standards, source-grounded explanations, and evidence review, with final verification against official BIS sources.*

</div>
