import time
import datetime
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from validator import (
    AnalyzeRequest, AnalyzeResponse,
    RecommendRequest, RecommendResponse,
    DetectIssuesRequest, DetectIssuesResponse,
    ForecastDemandRequest, ForecastDemandResponse,
    DetectAnomaliesRequest, DetectAnomaliesResponse
)
import ai_engine

app = FastAPI(title="Retail Intelligence Decision Engine")

START_TIME = time.time()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time_proc = time.perf_counter()
    response = await call_next(request)
    process_time_ms = (time.perf_counter() - start_time_proc) * 1000
    cold_start_ms = (time.time() - START_TIME) * 1000
    response.headers["X-Processing-Time-Ms"] = f"{process_time_ms:.2f}"
    response.headers["X-Cold-Start-Ms"] = f"{cold_start_ms:.2f}"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}")
    # Don't expose stack traces
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Rejects malformed input with clear error messages"""
    return JSONResponse(
        status_code=422,
        content={"detail": "Malformed input provided", "errors": exc.errors()},
    )

@app.get("/health")
async def health():
    uptime_seconds = time.time() - START_TIME
    return {
        "status": "ok",
        "uptime_seconds": round(uptime_seconds, 2),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    data_dict = [item.model_dump() for item in request.data]
    result = await ai_engine.analyze_sales(data_dict)
    background_tasks.add_task(ai_engine.log_to_gcs, "/analyze", request.model_dump(), result)
    return AnalyzeResponse(**result)

@app.post("/recommend", response_model=RecommendResponse)
async def recommend(request: RecommendRequest, background_tasks: BackgroundTasks):
    result = await ai_engine.recommend_products(request.user_id, request.purchase_history)
    background_tasks.add_task(ai_engine.log_to_gcs, "/recommend", request.model_dump(), result)
    return RecommendResponse(**result)

@app.post("/detect-issues", response_model=DetectIssuesResponse)
async def detect_issues(request: DetectIssuesRequest, background_tasks: BackgroundTasks):
    result = await ai_engine.detect_issues(request.store_id, request.inventory_levels)
    background_tasks.add_task(ai_engine.log_to_gcs, "/detect-issues", request.model_dump(), result)
    return DetectIssuesResponse(**result)

@app.post("/forecast-demand", response_model=ForecastDemandResponse)
async def forecast_demand(request: ForecastDemandRequest, background_tasks: BackgroundTasks):
    result = await ai_engine.forecast_demand(request.product_name, request.past_sales)
    background_tasks.add_task(ai_engine.log_to_gcs, "/forecast-demand", request.model_dump(), result)
    return ForecastDemandResponse(**result)

@app.post("/detect-anomalies", response_model=DetectAnomaliesResponse)
async def detect_anomalies(request: DetectAnomaliesRequest, background_tasks: BackgroundTasks):
    result = await ai_engine.detect_anomalies(request.product_name, request.past_sales)
    background_tasks.add_task(ai_engine.log_to_gcs, "/detect-anomalies", request.model_dump(), result)
    return DetectAnomaliesResponse(**result)

import os
if not os.path.exists("web_ui"):
    os.makedirs("web_ui")
app.mount("/", StaticFiles(directory="web_ui", html=True), name="static")
