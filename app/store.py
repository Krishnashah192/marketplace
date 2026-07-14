"""In-memory data store with a seeded catalog.

Swap for a real database in production; the interface is intentionally simple.
"""
import time
import uuid

MODELS: dict[str, dict] = {}
REVIEWS: dict[str, list[dict]] = {}
ESCROWS: dict[str, dict] = {}
BUNDLES: dict[str, dict] = {}
DRIFT_SUBS: dict[str, list[dict]] = {}
SANDBOX_QUOTA: dict[str, int] = {}  # model_id -> remaining free trials

SANDBOX_FREE_TRIALS = 5


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def seed() -> None:
    catalog = [
        dict(id="m_atlas", name="Atlas-7B", vendor="OpenForge", category="LLM",
             description="General-purpose reasoning model, strong at code.",
             parent_id=None, pricing_mode="per_outcome", base_price_usd=0.012,
             reservation_price_usd=0.008, benchmark_score=86.4, uptime_pct=99.95,
             energy_wh_per_1k_tokens=0.9, sla_min_quality=0.9),
        dict(id="m_atlas_med", name="Atlas-Med-7B", vendor="HelixAI", category="Healthcare",
             description="Atlas fine-tuned on clinical literature.",
             parent_id="m_atlas", pricing_mode="per_outcome", base_price_usd=0.03,
             reservation_price_usd=0.02, benchmark_score=91.2, uptime_pct=99.9,
             energy_wh_per_1k_tokens=1.1, sla_min_quality=0.95),
        dict(id="m_atlas_med_ped", name="Atlas-Peds", vendor="HelixAI", category="Healthcare",
             description="Pediatrics specialization of Atlas-Med.",
             parent_id="m_atlas_med", pricing_mode="subscription", base_price_usd=199.0,
             reservation_price_usd=149.0, benchmark_score=93.7, uptime_pct=99.8,
             energy_wh_per_1k_tokens=1.1, sla_min_quality=0.95),
        dict(id="m_pixel", name="PixelSmith-XL", vendor="Lumina Labs", category="Image",
             description="Text-to-image with layout control.",
             parent_id=None, pricing_mode="per_call", base_price_usd=0.04,
             reservation_price_usd=0.025, benchmark_score=88.1, uptime_pct=99.7,
             energy_wh_per_1k_tokens=6.5, sla_min_quality=0.8),
        dict(id="m_scribe", name="Scribe-Legal", vendor="LexMachina", category="Legal",
             description="Contract analysis and clause extraction agent.",
             parent_id=None, pricing_mode="per_outcome", base_price_usd=0.5,
             reservation_price_usd=0.35, benchmark_score=84.9, uptime_pct=99.99,
             energy_wh_per_1k_tokens=1.4, sla_min_quality=0.92),
    ]
    for m in catalog:
        MODELS[m["id"]] = m
        REVIEWS[m["id"]] = []
        SANDBOX_QUOTA[m["id"]] = SANDBOX_FREE_TRIALS

    REVIEWS["m_atlas"].extend([
        dict(rating=5, comment="Reliable outcomes, negotiation API saved us 20%.",
             verified_purchase=True, ts=time.time() - 86400 * 3),
        dict(rating=4, comment="Great for code tasks.", verified_purchase=True,
             ts=time.time() - 86400 * 40),
    ])
    REVIEWS["m_pixel"].append(
        dict(rating=3, comment="Quality drifted last month.", verified_purchase=False,
             ts=time.time() - 86400 * 10))


seed()
