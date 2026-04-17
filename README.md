# Retail AI Assistant Backend

## Vertical
Retail

## Problem Statement
Retail stores and e-commerce platforms generate massive amounts of data ranging from product sales to inventory levels and user purchase histories. Extracting actionable insights, personalized recommendations, and detecting supply chain issues from this data is challenging and resource-intensive using traditional deterministic methods.

## Approach
This project leverages Generative AI to interpret unstructured and structured retail data. By wrapping the Google Gemini API within a highly scalable FastAPI Python backend, we translate complex prompts into structured JSON outputs that can be readily consumed by frontend applications or down-stream reporting tools. Key endpoints are provided for general analysis, recommendation, and inventory issue detection.

## How It Works
The application exposes RESTful endpoints using FastAPI:
- `/analyze`: Accepts product sales data and returns insights with percentage-based performance metrics.
- `/recommend`: Interprets user purchase history to suggest products with a confidence score.
- `/detect-issues`: Analyzes store inventory levels to detect anomalies such as out-of-stock or overstocked items.
Input and output parsing is strictly validated using Pydantic, ensuring only properly formatted requests are processed and JSON structured insights are returned. 

## Google Services Used
- **Google Gemini API**: Utilized to provide the AI reasoning engine, interpreting the contextual retail data and mapping it into predefined JSON schemas using prompt engineering configuration.

## Assumptions
- The Google Gemini API key is provided securely through the `GEMINI_API_KEY` environment variable.
- Incoming data structures align with standard retail terminology (e.g., product identifiers, sales volume, revenue).
- The client application handles the actual enforcement of the returned insights (e.g. reordering inventory based on a detected issue).

## Local Setup
1. Clone this repository to your local machine.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Gemini API key:
   ```bash
   # Windows PowerShell
   $env:GEMINI_API_KEY="your_actual_api_key_here"
   
   # Linux/macOS
   export GEMINI_API_KEY="your_actual_api_key_here"
   ```
4. Run the development server:
   ```bash
   uvicorn main:app --reload --port 8080
   ```

## Sample cURL Commands

**Health Check**
```bash
curl -X GET http://localhost:8080/health
```

**Analyze Sales**
```bash
curl -X POST http://localhost:8080/analyze \
     -H "Content-Type: application/json" \
     -d '{"data":[{"product_id":"123","product_name":"Wireless Mouse","sales_volume":450,"revenue":11250.00}]}'
```

**Recommend Products**
```bash
curl -X POST http://localhost:8080/recommend \
     -H "Content-Type: application/json" \
     -d '{"user_id":"u-991","purchase_history":["laptop","mousepad"]}'
```

**Detect Issues**
```bash
curl -X POST http://localhost:8080/detect-issues \
     -H "Content-Type: application/json" \
     -d '{"store_id":"store-east","inventory_levels":{"item-A":2,"item-B":5000}}'
```
