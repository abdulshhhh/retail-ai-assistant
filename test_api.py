import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "timestamp" in data
    assert "X-Cold-Start-Ms" in response.headers
    assert "X-Processing-Time-Ms" in response.headers

def test_analyze_valid():
    payload = {
        "data": [
            {"product_id": "p1", "product_name": "Widget", "sales_volume": 100, "revenue": 1500.0}
        ]
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "insight" in data["results"][0]

def test_analyze_invalid():
    payload = {
        "data": [
            {"product_id": "p1", "sales_volume": -10} # Missing required fields and negative volume
        ]
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "Malformed input provided" in data["detail"]

def test_recommend_valid():
    payload = {"user_id": "u123", "purchase_history": ["p1", "p2"]}
    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_recommend_invalid():
    payload = {"purchase_history": ["p1"]} # Missing user_id
    response = client.post("/recommend", json=payload)
    assert response.status_code == 422

def test_detect_issues_valid():
    payload = {"store_id": "s1", "inventory_levels": {"p1": 5}}
    response = client.post("/detect-issues", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_detect_issues_invalid():
    # Empty string is invalid mapping and min_length requirement handling
    payload = {"store_id": "s1", "inventory_levels": {}} 
    response = client.post("/detect-issues", json=payload)
    assert response.status_code == 422

def test_forecast_demand_valid():
    payload = {"product_name": "Dal", "past_sales": [10, 12, 15, 14, 18, 20, 25]}
    response = client.post("/forecast-demand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["trend"] in ["increasing", "decreasing", "stable"]
    assert "predicted_demand" in data
    assert "intelligence" in data
    assert "insight" in data["intelligence"]

def test_forecast_demand_invalid_length():
    # Only 3 days, requirements say 7-14
    payload = {"product_name": "Dal", "past_sales": [10, 12, 15]}
    response = client.post("/forecast-demand", json=payload)
    assert response.status_code == 422

def test_detect_anomalies_valid():
    payload = {"product_name": "Rice", "past_sales": [50, 52, 100, 55]} 
    response = client.post("/detect-anomalies", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "anomaly_detected" in data
    assert "impact" in data
    assert data["intelligence"]["action"] is not None

def test_calculate_trend_rule():
    from ai_engine import calculate_trend
    assert calculate_trend([10, 20]) == "increasing"
    assert calculate_trend([20, 10]) == "decreasing"
    assert calculate_trend([10, 10]) == "stable"

def test_detect_rule_based_anomaly():
    from ai_engine import detect_rule_based_anomaly
    # Test spike > 30%
    b, t, i = detect_rule_based_anomaly([100, 140]) 
    assert b == True
    assert t == "spike"
    
    # Test drop > 30%
    b, t, i = detect_rule_based_anomaly([100, 60]) 
    assert b == True
    assert t == "drop"
    
    # Normal change
    b, t, i = detect_rule_based_anomaly([100, 110])
    assert b == False
