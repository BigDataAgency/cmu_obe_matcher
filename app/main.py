from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import router

app = FastAPI(
    title="Company-CLO Matcher API",
    description="Match companies to relevant Course Learning Outcomes (CLOs) and Program Learning Outcomes (PLOs)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["CLO Matcher"])

@app.get("/")
def read_root():
    return {"message": "Company-CLO Matcher API", "docs": "/docs", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
