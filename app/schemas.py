"""Pydantic schemas for the NeuralBazaar API."""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class ModelListing(BaseModel):
    id: str
    name: str
    vendor: str
    category: str
    description: str
    parent_id: Optional[str] = None  # Model DNA: lineage pointer
    pricing_mode: Literal["per_call", "per_outcome", "subscription"] = "per_outcome"
    base_price_usd: float = Field(ge=0)
    reservation_price_usd: float = Field(ge=0)  # seller's floor for negotiation
    benchmark_score: float = Field(ge=0, le=100)
    uptime_pct: float = Field(ge=0, le=100)
    energy_wh_per_1k_tokens: float = Field(ge=0)
    sla_min_quality: float = Field(ge=0, le=1, default=0.85)


class Review(BaseModel):
    model_id: str
    rating: float = Field(ge=1, le=5)
    comment: str = ""
    verified_purchase: bool = False


class NegotiationOffer(BaseModel):
    model_id: str
    offered_price_usd: float = Field(gt=0)
    volume: int = Field(gt=0, description="Committed monthly call volume")


class NegotiationResult(BaseModel):
    status: Literal["accepted", "counteroffer", "rejected"]
    agreed_price_usd: Optional[float] = None
    counter_price_usd: Optional[float] = None
    seller_message: str


class SandboxRequest(BaseModel):
    model_id: str
    prompt: str


class EscrowCreate(BaseModel):
    model_id: str
    buyer: str
    amount_usd: float = Field(gt=0)


class EscrowSettle(BaseModel):
    escrow_id: str
    measured_quality: float = Field(ge=0, le=1)


class BundleCreate(BaseModel):
    name: str
    model_ids: list[str] = Field(min_length=2)


class DriftSubscription(BaseModel):
    model_id: str
    email: str
    threshold_pct: float = Field(gt=0, le=50, default=5.0)


class OutcomeReport(BaseModel):
    model_id: str
    total_calls: int = Field(gt=0)
    successful_outcomes: int = Field(ge=0)
