from fastapi import FastAPI

app = FastAPI(
    title="Vantict Sniper",
    description="AI Technical Interview Script Generator",
    version="4.0.0",
)


@app.get("/")
async def root():
    return {"service": "vantict-sniper", "version": "4.0.0"}
