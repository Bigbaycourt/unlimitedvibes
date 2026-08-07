"""
Unlimited Vibes - FastAPI Application

Social app backend with:
- Compliance monitoring & content moderation
- Equity & cap table management
- API cost optimization
"""

from fastapi import FastAPI

from app.routes import compliance, equity, costs

app = FastAPI(
    title="Unlimited Vibes",
    description="Social app backend: compliance, equity, cost optimization",
    version="0.1.0",
)

# Register routers
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])
app.include_router(equity.router, prefix="/api/equity", tags=["equity"])
app.include_router(costs.router, prefix="/api/costs", tags=["costs"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}
