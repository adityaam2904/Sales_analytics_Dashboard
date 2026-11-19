from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import test_connection
from app.routers import upload 
from app.routers import etl
from app.routers import dashboard
from app.routers import data
app = FastAPI(
    title="Sales Analytics API",
    description="Backend API for the Sales Analytics Dashboard",
    version="1.0.0"
)

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://localhost:5173",
                   "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    test_connection()

app.include_router(upload.router)
app.include_router(etl.router)
app.include_router(dashboard.router)
app.include_router(data.router)
@app.get("/")
def root():
    return {"message": "Sales Analytics API is running ✅"}

@app.get("/health")
def health():
    return {"status": "ok"}