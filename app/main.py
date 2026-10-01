from fastapi import FastAPI


app = FastAPI(
    title="Shop Management SaaS API",
    version="1.0.0",
)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Shop Management SaaS API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }