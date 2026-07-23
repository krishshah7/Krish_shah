# Civic AI Companion

A GenAI + Agentic AI civic platform for Indian citizens: chat with an AI
about government schemes, file civic complaints, and track their status.

**Note on origin:** this project's concept was inspired by an open-source
hackathon submission ("Nagrik AI") solving the same civic-tech problem
statement. The implementation here is independently written using a
different stack (Python/Streamlit/SQLite/LangChain instead of
Next.js/Firebase/Groq) and a smaller, custom-curated dataset - built as a
personal learning project, not a copy of that codebase.

## Features

**1. AI Civic Companion (Chat)**
- RAG-grounded chat over a curated dataset of 12 Indian government schemes
- Tool-calling agent: retrieves relevant schemes, then optionally calls an
  `check_eligibility` tool to reason about whether the user qualifies based
  on details they share
- Cites the official source link for every scheme mentioned

**2. File a Complaint**
- Citizens describe a civic issue + location
- An LLM automatically classifies urgency (Critical / Medium / Low) -
  no manual triage
- Stored in a local SQLite database with a unique tracking ID

**3. Track a Complaint**
- Look up any complaint by ID, see status/category/details

## Why this project 

Demonstrates the two core patterns of applied Gen AI + Agentic AI:
- **RAG**: grounding LLM answers in a real knowledge base instead of
  letting it hallucinate scheme details
- **Tool-calling agent**: the LLM decides when to search vs. when to
  reason about eligibility, rather than following a fixed script
- **LLM-based classification**: using a model for structured labeling
  (urgency triage) instead of manual rules

## Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```
You'll need an OpenAI API key (entered in the sidebar at runtime).

## Tech stack
Python · LangChain · OpenAI API · ChromaDB · SQLite · Streamlit

## Possible extensions
- Multilingual support (detect + respond in Hindi/regional languages)
- Voice input for low-literacy users
- Admin view for staff to update complaint statuses
- Swap SQLite for a hosted DB if deploying beyond local demo
