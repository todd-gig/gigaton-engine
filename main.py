"""Gigaton Engine — unified FastAPI application."""
from fastapi import FastAPI

from integration.wiring import wire_all
from margin_optimization.api import router as margin_router
from multi_agent.api import router as agents_router
from pricing_engine.api import router as pricing_router
from trigger_engine.api import router as events_router

app = FastAPI(
    title="Gigaton Engine",
    description="Pricing engine, margin optimization, multi-agent coordination, and real-time event processing.",
    version="1.0.0",
)

# Mount all routers
app.include_router(pricing_router)
app.include_router(margin_router)
app.include_router(agents_router)
app.include_router(events_router)


@app.on_event("startup")
def startup() -> None:
    wire_all()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}
