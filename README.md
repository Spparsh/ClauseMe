# ClauseMe

**AI-powered contract risk detector.**

ClauseMe is an AI agent that reads contracts, identifies potentially risky clauses, explains why they matter, and gives users a quick, easy-to-understand risk report before they sign.

## Features

* Detects risky contract clauses
* Categorizes risks by severity
* Explains why a clause was flagged
* Provides an AI investigation trail
* Ask the agent questions about flagged clauses
* Demo contract included
* Optional LLM-powered analysis

## Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Python, FastAPI
* **AI:** Rule-based agent + OpenAI API
* **API:** REST

## How It Works

```text
Contract
   ↓
Clause Detection
   ↓
Risk Investigation
   ↓
Context Analysis
   ↓
AI Explanation
   ↓
Risk Report
```

## Run Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open `frontend/index.html` using VS Code Live Server.

> ClauseMe is a prototype for contract analysis and does not provide legal advice.
