"""Business logic: karma, negotiation, escrow, green score, lineage, pricing."""
import hashlib
import math
import time

from . import store


# ---------- Model Karma (trust score) ----------

def karma(model_id: str) -> float:
    """Blend benchmarks (50%), recency-decayed reviews (35%), uptime (15%).

    Verified-purchase reviews weigh 3x unverified ones, and every review's
    influence halves each 30 days — making review bombing ineffective.
    """
    m = store.MODELS[model_id]
    bench = m["benchmark_score"]  # 0-100
    uptime = m["uptime_pct"]      # 0-100

    now = time.time()
    num, den = 0.0, 0.0
    for r in store.REVIEWS.get(model_id, []):
        age_days = (now - r["ts"]) / 86400
        decay = 0.5 ** (age_days / 30)
        weight = (3.0 if r["verified_purchase"] else 1.0) * decay
        num += weight * (r["rating"] / 5 * 100)
        den += weight
    review_score = num / den if den else bench  # no reviews -> neutral

    return round(0.5 * bench + 0.35 * review_score + 0.15 * uptime, 1)


# ---------- Carbon transparency ----------

def green_score(model_id: str) -> dict:
    """Map energy use to an A–E grade. Lower Wh/1K tokens is better."""
    wh = store.MODELS[model_id]["energy_wh_per_1k_tokens"]
    grade = "A" if wh < 1 else "B" if wh < 2 else "C" if wh < 4 else "D" if wh < 8 else "E"
    return {"energy_wh_per_1k_tokens": wh, "grade": grade,
            "co2_g_per_1k_tokens": round(wh * 0.4, 3)}  # ~0.4 gCO2/Wh grid avg


# ---------- AI-to-AI negotiation ----------

def negotiate(model_id: str, offered: float, volume: int) -> dict:
    """Seller agent with a volume-aware concession strategy.

    High committed volume lowers the seller's effective floor by up to 15%.
    Offers >= floor are accepted; offers within 30% of the floor get a
    counteroffer meeting the buyer halfway; lowball offers are rejected.
    """
    m = store.MODELS[model_id]
    floor = m["reservation_price_usd"]
    volume_discount = min(0.15, math.log10(max(volume, 1)) * 0.03)
    effective_floor = round(floor * (1 - volume_discount), 6)

    if offered >= effective_floor:
        price = round(min(offered, m["base_price_usd"]), 6)
        return dict(status="accepted", agreed_price_usd=price, counter_price_usd=None,
                    seller_message=f"Deal at ${price} (volume discount "
                                   f"{volume_discount:.0%} applied).")
    if offered >= effective_floor * 0.7:
        counter = round((offered + effective_floor) / 2, 6)
        return dict(status="counteroffer", agreed_price_usd=None,
                    counter_price_usd=counter,
                    seller_message=f"Can't do ${offered}, but I'll meet you at ${counter}.")
    return dict(status="rejected", agreed_price_usd=None, counter_price_usd=None,
                seller_message="Offer is below our economics even at that volume.")


# ---------- Outcome-based billing ----------

def outcome_invoice(model_id: str, total_calls: int, successes: int) -> dict:
    m = store.MODELS[model_id]
    if m["pricing_mode"] != "per_outcome":
        billable, note = total_calls, "Model bills per call."
    else:
        billable, note = successes, "Only successful outcomes are billed."
    amount = round(billable * m["base_price_usd"], 4)
    return dict(model_id=model_id, total_calls=total_calls,
                successful_outcomes=successes, billable_units=billable,
                amount_usd=amount, note=note)


# ---------- Quality-assured escrow ----------

def settle_escrow(escrow_id: str, measured_quality: float) -> dict:
    e = store.ESCROWS[escrow_id]
    if e["status"] != "held":
        return e
    sla = store.MODELS[e["model_id"]]["sla_min_quality"]
    e["measured_quality"] = measured_quality
    e["status"] = "released_to_seller" if measured_quality >= sla else "refunded_to_buyer"
    e["settled_at"] = time.time()
    return e


# ---------- Model DNA / lineage ----------

def lineage(model_id: str) -> list[dict]:
    """Walk parent pointers from the model up to its root ancestor."""
    chain, seen = [], set()
    cur = store.MODELS.get(model_id)
    while cur and cur["id"] not in seen:
        seen.add(cur["id"])
        chain.append({"id": cur["id"], "name": cur["name"], "vendor": cur["vendor"]})
        cur = store.MODELS.get(cur["parent_id"]) if cur["parent_id"] else None
    return chain


# ---------- Skill bundles ----------

def bundle_price(model_ids: list[str]) -> dict:
    """Sum base prices, then apply a composability discount of 5% per extra model
    (capped at 20%)."""
    total = sum(store.MODELS[mid]["base_price_usd"] for mid in model_ids)
    discount = min(0.20, 0.05 * (len(model_ids) - 1))
    return dict(list_price_usd=round(total, 4), discount_pct=round(discount * 100, 1),
                bundle_price_usd=round(total * (1 - discount), 4))


# ---------- Sandbox (deterministic mock inference) ----------

def sandbox_run(model_id: str, prompt: str) -> dict:
    quota = store.SANDBOX_QUOTA.get(model_id, 0)
    if quota <= 0:
        return dict(ok=False, error="Free trial quota exhausted — purchase to continue.")
    store.SANDBOX_QUOTA[model_id] = quota - 1
    m = store.MODELS[model_id]
    digest = hashlib.sha256(f"{model_id}:{prompt}".encode()).hexdigest()[:8]
    return dict(ok=True, model=m["name"], trials_left=store.SANDBOX_QUOTA[model_id],
                output=f"[{m['name']} demo:{digest}] Simulated response to: "
                       f"{prompt[:120]}")
