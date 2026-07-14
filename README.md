# NeuralBazaar — The AI Marketplace

A marketplace for AI models and agents with features you won't find on existing platforms.

## Unique Features

| Feature | What it does |
|---|---|
| **Outcome-Based Pricing** | Pay only for *successful* outcomes, not raw API calls. Failed inferences cost nothing. |
| **AI-to-AI Negotiation** | Buyer agents negotiate price with seller agents in real time using concession strategies. |
| **Model Karma™** | Trust score blending verified benchmarks, recency-decayed reviews, and uptime — resistant to review bombing. |
| **Model DNA / Lineage** | Full provenance graph: see every base model and fine-tune a model descends from. |
| **Quality-Assured Escrow** | Funds held in escrow and auto-refunded if the model misses its quality SLA. |
| **Carbon Transparency** | Energy per 1K tokens and a Green Score for every listing. |
| **Skill Bundles** | Compose multiple models into pipelines and sell the bundle with a composability discount. |
| **Drift Alerts** | Subscribe to performance-drift notifications for any model you depend on. |
| **Try-Before-You-Buy Sandbox** | Run capped free trials against any model before purchasing. |

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the UI, or http://localhost:8000/docs for the interactive API docs.

## Project Layout

```
app/
  main.py      # FastAPI app + all API routes
  schemas.py   # Pydantic request/response models
  store.py     # In-memory data store + seed catalog
  services.py  # Karma, negotiation, escrow, pricing, lineage logic
static/        # Single-page frontend (no build step)
```
