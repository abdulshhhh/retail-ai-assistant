from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# --- Shared Intelligence Interface ---
class IntelligenceResult(BaseModel):
    insight: str = Field(..., description="Core actionable insight string")
    action: str = Field(..., description="Recommended action")
    confidence: str = Field(..., description="Confidence represented as a percentage string, e.g. '85%'")
    reasoning: str = Field(..., description="Short explanation or reasoning")

# --- Analyze Endpoints ---
class ProductSalesData(BaseModel):
    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    sales_volume: int = Field(..., ge=0)
    revenue: float = Field(..., ge=0.0)

class AnalyzeRequest(BaseModel):
    data: List[ProductSalesData] = Field(..., min_length=1)

class AnalyzeResponse(BaseModel):
    results: List[IntelligenceResult]

# --- Recommend Endpoints ---
class RecommendRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    purchase_history: List[str] = Field(default_factory=list)

class RecommendResponse(BaseModel):
    results: List[IntelligenceResult]

# --- Issue Detection Endpoints ---
class DetectIssuesRequest(BaseModel):
    store_id: str = Field(..., min_length=1)
    inventory_levels: Dict[str, int] = Field(..., min_length=1)

class DetectIssuesResponse(BaseModel):
    results: List[IntelligenceResult]

# --- Forecast Demand Endpoints ---
class ForecastDemandRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    past_sales: List[int] = Field(..., min_length=7, max_length=14, description="Sales for the past 7-14 days")

class ForecastDemandResponse(BaseModel):
    predicted_demand: int = Field(..., description="Predicted integer value representing demand")
    trend: str = Field(..., description="trend based on rule calculation")
    intelligence: IntelligenceResult

# --- Detect Anomalies Endpoints ---
class DetectAnomaliesRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    past_sales: List[int] = Field(..., min_length=1)

class DetectAnomaliesResponse(BaseModel):
    anomaly_detected: bool
    anomaly_type: str
    impact: str
    intelligence: IntelligenceResult
