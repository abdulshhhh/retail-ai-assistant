import os
import httpx
import json
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GCS_BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME")
# Provide an optional access token for local testing without the need for cloud native auth libraries
GCS_ACCESS_TOKEN = os.environ.get("GCS_ACCESS_TOKEN") 

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

SYSTEM_PROMPT = """You are an expert retail analyst specializing in Indian kirana stores and e-commerce platforms. 
Consider: 
- Festival demand spikes (Diwali, Pongal) 
- Local buying behavior 
- Stock shortages and overstock risks

Always return: 
- structured JSON only 
- actionable recommendation 
- confidence percentage 
- one-line reasoning"""

async def call_gemini(prompt: str) -> dict:
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set. Returning mock response.")
        return _get_mock_response(prompt)
        
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nTask:\n{prompt}"}]}
        ],
        "generationConfig": {"response_mime_type": "application/json"}
    }
    params = {"key": GEMINI_API_KEY}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(API_URL, headers=headers, params=params, json=payload, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            raise ValueError(f"AI Engine Error: {e}")

def _get_mock_response(prompt: str) -> dict:
    intelligence = {"insight": "Mock insight", "action": "Mock action", "confidence": "85%", "reasoning": "Mocking because NO_KEY"}
    if "Forecast" in prompt:
        return {"predicted_demand": 150, "intelligence": intelligence}
    elif "Detect anomalies" in prompt:
        return {"intelligence": intelligence}
    return {"results": [intelligence]}

# Rule base heuristics
def calculate_trend(past_sales: list[int]) -> str:
    if len(past_sales) < 2: return "stable"
    if past_sales[-1] > past_sales[0]: return "increasing"
    if past_sales[-1] < past_sales[0]: return "decreasing"
    return "stable"

def detect_rule_based_anomaly(past_sales: list[int]) -> tuple:
    if len(past_sales) < 2: return False, "none", "low"
    
    for i in range(1, len(past_sales)):
        prev = past_sales[i-1]
        curr = past_sales[i]
        if prev == 0:
            if curr > 0: return True, "spike", "high"
            continue
        change = (curr - prev) / prev
        if change > 0.3:
            return True, "spike", "high" if change > 0.5 else "medium"
        elif change < -0.3:
            return True, "drop", "high" if change < -0.5 else "medium"
    return False, "none", "low"

# Core Functions
async def analyze_sales(data: list) -> dict:
    prompt = f"Analyze the following sales data. Return format schema: {{\"results\": [{{\"insight\": \"string\", \"action\": \"string\", \"confidence\": \"string\", \"reasoning\": \"string\"}}]}}. Data: {data}"
    return await call_gemini(prompt)

async def recommend_products(user_id: str, history: list) -> dict:
    prompt = f"Recommend products for user {user_id} with history {history}. Return format schema: {{\"results\": [{{\"insight\": \"string\", \"action\": \"string\", \"confidence\": \"string\", \"reasoning\": \"string\"}}]}}."
    return await call_gemini(prompt)

async def detect_issues(store_id: str, inventory: dict) -> dict:
    prompt = f"Detect inventory issues for store {store_id} with inventory {inventory}. Return format schema: {{\"results\": [{{\"insight\": \"string\", \"action\": \"string\", \"confidence\": \"string\", \"reasoning\": \"string\"}}]}}."
    return await call_gemini(prompt)

async def forecast_demand(product_name: str, past_sales: list[int]) -> dict:
    trend = calculate_trend(past_sales)
    prompt = f"Forecast demand for '{product_name}' using past sales {past_sales}. The rule-based system detected a '{trend}' trend. Generate a reasonable predicted_demand integer. Return format schema: {{\"predicted_demand\": integer, \"intelligence\": {{\"insight\": \"string\", \"action\": \"string\", \"confidence\": \"string\", \"reasoning\": \"string\"}}}}."
    result = await call_gemini(prompt)
    result["trend"] = trend # ensure trend is overridden directly
    return result

async def detect_anomalies(product_name: str, past_sales: list[int]) -> dict:
    anom_bool, anom_type, impact = detect_rule_based_anomaly(past_sales)
    prompt = f"Detect anomalies for '{product_name}' using past sales {past_sales}. Rule system detected: anomaly={anom_bool}, type={anom_type}, impact={impact}. Provide reasoning for this finding. Return format schema: {{\"intelligence\": {{\"insight\": \"string\", \"action\": \"string\", \"confidence\": \"string\", \"reasoning\": \"string\"}}}}."
    result = await call_gemini(prompt)
    # Ensure correct types are injected statically from the rule engine
    result["anomaly_detected"] = anom_bool
    result["anomaly_type"] = anom_type
    result["impact"] = impact
    return result

# Lightweight GCS logging function
async def log_to_gcs(endpoint: str, request_data: dict, response_data: dict):
    if not GCS_BUCKET_NAME:
        return
        
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "endpoint": endpoint,
        "request": request_data,
        "response": response_data
    }
    
    filename = f"{endpoint.strip('/')}_{uuid.uuid4().hex[:8]}.json"
    
    # We fallback to expecting an explicit token when GCS testing locally/Cloud Run.
    token = GCS_ACCESS_TOKEN
    
    if not token:
        logger.warning(f"GCS_BUCKET_NAME={GCS_BUCKET_NAME} is set but GCS_ACCESS_TOKEN is missing. Skipping GCS upload.")
        return 
        
    url = f"https://storage.googleapis.com/upload/storage/v1/b/{GCS_BUCKET_NAME}/o?uploadType=media&name={filename}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=headers, json=payload, timeout=5.0)
            res.raise_for_status()
            logger.info(f"Successfully logged {filename} to bucket {GCS_BUCKET_NAME}")
    except Exception as e:
        logger.error(f"GCS Logging failed: {e}")
