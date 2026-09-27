# BIScope

### AI-Powered Intelligent Assistant for Indian Standards and BIS Services

BIScope is an intelligent standards-assistance platform designed to help **industries and consumers discover, understand, and review information related to Indian Standards and BIS services**.

It bridges the gap between everyday product terminology and structured BIS information through intelligent terminology normalization, standard discovery, requirement exploration, evidence review, and a context-aware AI assistant.

> **BIScope is an information and decision-support system. It does not replace official BIS certification, testing, inspection, regulatory processes, or legal requirements.**

---

## Overview

Finding the appropriate Indian Standard can be difficult when users do not know the relevant standard number, official terminology, product classification, or applicable requirements.

BIScope addresses this problem through a unified workflow:

**Discover → Understand → Verify → Review → Act**

A user can describe a product or requirement using natural language, after which BIScope identifies relevant supported product information, surfaces associated standards and requirements, and provides contextual explanations and evidence-review assistance.

---

## Key Capabilities

### Intelligent Terminology Bridge

Converts everyday product terminology into supported BIS-oriented terminology.

The terminology layer supports:

* Synonyms and alternate terms
* Text normalization
* Common spelling variations
* Typo recovery
* Ambiguous terminology detection
* Unsupported-term handling
* Confidence-based matching

The system does not generate unsupported standards when a reliable product match is unavailable.

---

### Smart Search Recovery

Improves search reliability by handling common variations in user input, including:

* Case differences
* Extra whitespace
* Common spelling mistakes
* Everyday terminology
* Supported synonyms

This allows users to search naturally without needing to know the exact wording used in the underlying dataset.

---

### Candidate Standard Discovery

Once a supported product is identified, BIScope can surface associated standard information such as:

* Indian Standard number
* Standard title
* Edition/year
* Status
* Scope
* Product association

The standard information is retrieved from structured BIScope data rather than being fabricated by the AI layer.

---

### Standard Context & Explanation

BIScope provides contextual explanations for why a standard is associated with a selected product.

Depending on the available data, the explanation can consider:

* Product category
* Material
* Intended use
* Product characteristics
* Standard scope
* Terminology match

This makes the relationship between a product and its associated standard easier to understand.

---

### Alternative Candidate Analysis

BIScope can identify mismatches between a selected product and alternative candidate information.

This helps users understand which product characteristics or contextual conditions do not align with a candidate.

---

### Requirement Explorer

Users can inspect detailed requirements associated with supported products and standards.

Requirement records can include:

* Requirement ID
* Requirement name
* Description
* Clause/reference
* Conditions
* Comparison information
* Evidence information
* Verification status
* Notes

The current MVP contains **117 detailed requirement records across 18 supported product records**.

---

### Evidence Review

BIScope provides an evidence-review workflow for supported uploaded documents.

Evidence content is analyzed against requirement-related information to identify:

* Relevant matches
* Missing information
* Requirements requiring review
* Evidence-related observations

Evidence matching is intended to assist review. It is **not a laboratory test, certification decision, or independent compliance determination**.

---

### Context-Aware AI Assistant

BIScope includes a conversational assistant that helps users understand the information available within the platform.

The assistant can provide contextual explanations for:

* BIScope functionality
* Products
* Standards
* Requirements
* Evidence-related information
* Terminology
* Standard relationships

The AI layer functions primarily as an **interaction and explanation layer**, while structured BIScope data remains the source of truth for supported records.

---

## System Workflow

```text
                         USER
                           │
                           ▼
              Natural-Language Product / Query
                           │
                           ▼
              ┌─────────────────────────┐
              │   Terminology Bridge    │
              │ Normalization & Recovery│
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  Product Identification │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Standard Discovery    │
              └────────────┬────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
       Standard Explanation     Requirement Explorer
                                      │
                                      ▼
                             Evidence Review
                                      │
                                      ▼
                           Context-Aware Assistant
                                      │
                                      ▼
                              USER UNDERSTANDING
```

---

## Architecture

BIScope follows a modular frontend-backend architecture.

```text
┌─────────────────────────────────────────────────────────────┐
│                         BIScope UI                          │
│                  React + TypeScript + Vite                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                              REST
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                       │
├─────────────────────────────────────────────────────────────┤
│ API Layer                                                   │
│                                                             │
│  Terminology │ Search │ Standards │ Requirements │ Evidence │
└──────────────────────────────┬──────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       Terminology Data   Standards Data   Requirements Data
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    Evidence & AI Services
```

---

# Technology Stack

| **Layer**       | **Technology**                 |
| --------------- | ------------------------------ |
| Frontend        | React, TypeScript, HTML5, CSS3 |
| Build Tool      | Vite                           |
| Backend         | Python, FastAPI                |
| API Server      | Uvicorn                        |
| Data Processing | Python                         |
| AI Layer        | Context-aware AI service       |
| Testing         | Python `unittest`              |
| Version Control | Git, GitHub                    |

---

# Project Structure

```text
BIScope/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── backend/
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── detailed_requirements.json
│   │   ├── detailed_requirements.py
│   │   ├── requirements_data.py
│   │   └── terminology_data.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_chat.py
│   │   ├── bis_data.py
│   │   ├── detailed_requirements.py
│   │   ├── document_extractor.py
│   │   ├── evidence_mapping.py
│   │   ├── requirements.py
│   │   ├── standard_search.py
│   │   └── terminology.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_ai_chat.py
│       ├── test_api.py
│       ├── test_detailed_requirements.py
│       ├── test_evidence_mapping.py
│       ├── test_matrix.py
│       ├── test_real_world.py
│       └── test_terminology.py
│
├── scripts/
│   └── import_data.py
│
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── index.html
    ├── vite.config.ts
    │
    ├── public/
    │   ├── favicon.svg
    │   ├── icons.svg
    │   ├── logo-dark.png
    │   └── logo-light.png
    │
    └── src/
        ├── App.tsx
        ├── App.css
        ├── index.css
        ├── main.tsx
        ├── types.ts
        │
        ├── assets/
        │   ├── hero.png
        │   ├── react.svg
        │   └── vite.svg
        │
        └── lib/
            └── api.ts
```

---

# API Reference

BIScope exposes REST APIs through FastAPI.

### Terminology

```http
POST /api/v1/terminology/analyze
```

Analyzes and normalizes user terminology.

### Conversational Assistant

```http
POST /api/v1/chat
```

Processes context-aware conversational requests.

### Search

```http
GET /api/v1/search
```

Searches supported product and standard information.

### Standard Information

```http
GET /api/v1/standards/{standard_id}
```

Retrieves information associated with a standard.

```http
GET /api/v1/standards/{standard_id}/explanation
```

Provides contextual standard explanation.

```http
GET /api/v1/standards/{standard_id}/alternatives
```

Provides available alternative candidate information.

### Requirements

```http
GET /api/v1/requirements
```

Returns supported requirement information.

```http
GET /api/v1/requirements/{product_id}
```

Returns requirements associated with a product.

```http
GET /api/v1/requirements/{product_id}/detailed
```

Returns detailed requirement information.

### Evidence

```http
POST /api/v1/evidence/analyze
```

Analyzes uploaded evidence against available requirement information.

```http
POST /api/v1/evidence/upload
```

Handles supported evidence uploads.

---

# Application Views

BIScope currently provides the following primary workflows:

### Home

Entry point for product discovery and BIS-related queries.

### Explore

Displays product and associated standard information.

### Check Requirements

Provides detailed requirement information for supported products.

### Review Evidence

Allows users to review uploaded evidence against relevant requirements.

### Services

Provides access to available BIScope assistance workflows.

---

# Local Development

## Prerequisites

Install the following:

* Python 3.x
* Node.js
* npm
* Git

---

## Clone the Repository

```powershell
git clone https://github.com/sruthika-19/BIScope.git
cd BIScope
```

---

## Start the Backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## Start the Frontend

Open a second terminal:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The Vite development server will display the frontend URL in the terminal.

Typically:

```text
http://localhost:5173
```

---

## Database Setup

BIScope uses SQLite for local database-backed standard and product lookups. The generated `biscope.db` file is intentionally excluded from version control through `.gitignore`.

### Automatic Initialization

No manual database creation is required.

When the backend requires the database and `biscope.db` does not exist, BIScope automatically initializes the database and seeds the supported product and standard records from the existing local project data.

The database contains the project's 18 supported product records and their associated standard mappings.

### Manual Initialization

The database can also be rebuilt or re-seeded manually using the idempotent import script:

```bash
python scripts/import_data.py
```

---

# Configuration

The frontend uses the following backend URL by default:

```text
http://localhost:8000
```

To configure a different API origin, create:

```text
frontend/.env
```

and add:

```env
VITE_API_BASE=http://your-backend-url
```

Restart the frontend development server after changing the environment configuration.

---

# Testing

Run the backend test suite from the project root:

```powershell
cd backend
python -m unittest discover tests
```

The test suite covers:

* AI Assistant behavior
* API endpoints
* Database-backed data retrieval
* Detailed requirements
* Evidence mapping
* Requirement matrices
* Real-world scenarios
* Terminology matching

A successful run should conclude with:

```text
OK
```

---

# Data Integrity & Safety

BIScope follows a **source-grounded approach** to standards assistance.

### Structured data as the source of truth

Supported product, standard, and requirement information is retrieved from the application's structured dataset.

### No unsupported standard generation

BIScope is designed not to fabricate standard numbers, titles, requirements, or applicability information when a reliable supported match is unavailable.

### Verification status ≠ compliance

A record marked:

```text
Verified Source Available
```

indicates that a relevant source has been identified within the current dataset.

It does **not** indicate that a product has passed testing or received BIS certification.

### Evidence match ≠ certification

Evidence matching identifies relevant content for review. It does not independently establish technical compliance.

### Official BIS processes remain authoritative

Official BIS publications, applicable regulations, testing laboratories, certification procedures, and current authoritative documentation remain necessary for formal compliance and certification decisions.

---

# Current MVP Scope

The current implementation includes:

* **18 supported product records**
* **117 detailed requirement records**
* Terminology normalization
* Search recovery
* Candidate standard discovery
* Standard explanation
* Alternative candidate analysis
* Requirement exploration
* Evidence review
* Requirement-to-evidence mapping
* Context-aware AI assistance
* Responsive web interface
* Automated backend testing

---

# Limitations

BIScope is currently an **MVP/prototype**.

The current implementation does not represent the complete BIS ecosystem.

Limitations include:

* Limited structured product and standard coverage.
* Not every BIS standard is currently represented.
* Some information may require verification against current official BIS sources.
* Evidence analysis is limited to the information available in uploaded documents and the implemented matching logic.
* AI-generated explanations should not be treated as authoritative legal or regulatory interpretations.
* Formal certification and compliance decisions remain outside the scope of the application.
* Live synchronization with every BIS source is not assumed unless explicitly implemented and verified.

---

# Future Enhancements

Potential future development includes:

* Expanded BIS product and standard coverage.
* Enhanced official-source synchronization.
* Improved multilingual assistance.
* Expanded terminology and synonym coverage.
* Advanced document extraction.
* Clause-level evidence mapping.
* Improved amendment and standard-version tracking.
* Enhanced consumer-oriented BIS services.
* More comprehensive source traceability.
* Additional BIS service workflows.
* Improved accessibility and voice interaction.

---

# Smart India Hackathon 2026

BIScope was developed in response to the Smart India Hackathon 2026 problem statement:

> **AI-powered Intelligent Assistant for Indian Standards and BIS Services for Industries and Consumers**

The project focuses on reducing the complexity of discovering and understanding standards-related information while maintaining a clear distinction between **AI-assisted information discovery** and **official BIS certification or compliance decisions**.

---

# Project Status

**MVP / Prototype**

The current system provides an integrated frontend and FastAPI backend with structured BIS-oriented data, requirements, evidence review, and conversational assistance.

---

# License

See [`LICENSE`](LICENSE) for licensing information.

---

# Repository

**GitHub:**

https://github.com/sruthika-19/BIScope