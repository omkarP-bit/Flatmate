from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from config import settings
from database import health_check
from router import router

app = FastAPI(title="Flatmate – Expense Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dcv6944l3p636.cloudfront.net",
        "http://localhost:5173",
        "http://localhost:3000",
        "https://localhost",
        "capacitor://localhost",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    db_ok = health_check()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": settings.service_name,
        "db": db_ok,
    }


handler = Mangum(app)