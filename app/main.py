"""NeuralBazaar — AI Marketplace API."""
import time

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from . import schemas, services, store

app = FastAPI(title="NeuralBazaar", description="AI Marketplace API", version="0.1.0")


def _get_model_or_404(model_id: str) -> dict:
    m = store.MODELS.get(model_id)
    if not m:
        raise HTTPException(404, f"Unknown model '{model_id}'")
    return m


# ---------- Catalog ----------

@app.get("/api/models")
def list_models(category: str | None = None, q: str | None = None):
    out = []
    for m in store.MODELS.values():
        if category and m["category"].lower() != category.lower():
            continue
        if q and q.lower() not in (m["name"] + m["description"]).lower():
            continue
        out.append({**m, "karma": services.karma(m["id"]),
                    "green": services.green_score(m["id"])})
    return sorted(out, key=lambda x: -x["karma"])


@app.get("/api/models/{model_id}")
def get_model(model_id: str):
    m = _get_model_or_404(model_id)
    return {**m, "karma": services.karma(model_id),
            "green": services.green_score(model_id),
            "lineage": services.lineage(model_id),
            "reviews": store.REVIEWS.get(model_id, []),
            "sandbox_trials_left": store.SANDBOX_QUOTA.get(model_id, 0)}


@app.post("/api/models", status_code=201)
def publish_model(listing: schemas.ModelListing):
    if listing.id in store.MODELS:
        raise HTTPException(409, "Model id already exists")
    if listing.parent_id and listing.parent_id not in store.MODELS:
        raise HTTPException(422, "parent_id refers to unknown model")
    store.MODELS[listing.id] = listing.model_dump()
    store.REVIEWS[listing.id] = []
    store.SANDBOX_QUOTA[listing.id] = store.SANDBOX_FREE_TRIALS
    return store.MODELS[listing.id]


# ---------- Reviews & Karma ----------

@app.post("/api/reviews", status_code=201)
def add_review(review: schemas.Review):
    _get_model_or_404(review.model_id)
    entry = {**review.model_dump(exclude={"model_id"}), "ts": time.time()}
    store.REVIEWS[review.model_id].append(entry)
    return {"karma": services.karma(review.model_id)}


# ---------- AI-to-AI negotiation ----------

@app.post("/api/negotiate", response_model=schemas.NegotiationResult)
def negotiate(offer: schemas.NegotiationOffer):
    _get_model_or_404(offer.model_id)
    return services.negotiate(offer.model_id, offer.offered_price_usd, offer.volume)


# ---------- Outcome-based billing ----------

@app.post("/api/billing/outcome-invoice")
def outcome_invoice(report: schemas.OutcomeReport):
    _get_model_or_404(report.model_id)
    if report.successful_outcomes > report.total_calls:
        raise HTTPException(422, "successes cannot exceed total calls")
    return services.outcome_invoice(report.model_id, report.total_calls,
                                    report.successful_outcomes)


# ---------- Quality-assured escrow ----------

@app.post("/api/escrow", status_code=201)
def create_escrow(req: schemas.EscrowCreate):
    _get_model_or_404(req.model_id)
    eid = store.new_id("esc")
    store.ESCROWS[eid] = dict(id=eid, model_id=req.model_id, buyer=req.buyer,
                              amount_usd=req.amount_usd, status="held",
                              created_at=time.time())
    return store.ESCROWS[eid]


@app.post("/api/escrow/settle")
def settle_escrow(req: schemas.EscrowSettle):
    if req.escrow_id not in store.ESCROWS:
        raise HTTPException(404, "Unknown escrow")
    return services.settle_escrow(req.escrow_id, req.measured_quality)


# ---------- Skill bundles ----------

@app.post("/api/bundles", status_code=201)
def create_bundle(req: schemas.BundleCreate):
    for mid in req.model_ids:
        _get_model_or_404(mid)
    bid = store.new_id("bnd")
    store.BUNDLES[bid] = dict(id=bid, name=req.name, model_ids=req.model_ids,
                              **services.bundle_price(req.model_ids))
    return store.BUNDLES[bid]


@app.get("/api/bundles")
def list_bundles():
    return list(store.BUNDLES.values())


# ---------- Drift alerts ----------

@app.post("/api/drift/subscribe", status_code=201)
def subscribe_drift(sub: schemas.DriftSubscription):
    _get_model_or_404(sub.model_id)
    store.DRIFT_SUBS.setdefault(sub.model_id, []).append(sub.model_dump())
    return {"subscribed": True, "model_id": sub.model_id,
            "threshold_pct": sub.threshold_pct}


# ---------- Sandbox ----------

@app.post("/api/sandbox")
def sandbox(req: schemas.SandboxRequest):
    _get_model_or_404(req.model_id)
    result = services.sandbox_run(req.model_id, req.prompt)
    if not result["ok"]:
        raise HTTPException(402, result["error"])
    return result


# Frontend (served last so /api routes take precedence)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
