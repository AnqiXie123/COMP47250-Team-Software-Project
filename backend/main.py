from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chargers, energy, recommendations, traffic, infrastructure

app = FastAPI(title="EcoCharge Dublin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(chargers.router)
app.include_router(energy.router)
app.include_router(recommendations.router)
app.include_router(traffic.router)
app.include_router(infrastructure.router)
