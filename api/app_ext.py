from fastapi import FastAPI, HTTPException
from api.models import JobRequest, JobResponse
from main import main

app = FastAPI(title="Code Executor API (extended)")

@app.post("/execute", response_model=JobResponse)
def execute(req: JobRequest):
    try:
        result = main.execute(req.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/status/{job_id}", response_model=JobResponse)
def status(job_id: str):
    return main.status(job_id)

@app.get("/history")
def history():
    return main.history()
