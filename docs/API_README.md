# StockFlow API Documentation

**Base URL:** `https://tekpeek.duckdns.org`

---

## Authentication
Some endpoints require an API key. Pass your API key in the `X-API-KEY` header.

---

## Signal Engine Endpoints

### 1. Health Check
- **Method:** GET
- **Endpoint:** `/api/health`
- **Description:** Returns the health status of the signal engine service.
- **Response Example:**
```json
{
  "status": "OK",
  "timestamp": "2024-06-01T12:00:00Z"
}
```

---

### 2. Get Final Signal for Stock
- **Method:** GET
- **Endpoint:** `/api/{stock_id}`
- **Description:** Returns the combined signal analysis for a given stock (must end with `.NS`).
- **Query Parameters:**
  - `interval` (string, optional)
  - `period` (int, optional)
  - `window` (int, optional)
  - `num_std` (float, optional)
- **Response Example:**
```json
{
  "buy": "true",
  "signals": "MACD-1 & CMF; MACD-2",
  "reason": "No MACD crossover, CMF < 0",
  "strength": "Strong"
}
```

---

### 3. Get Individual Indicator for Stock
- **Method:** GET
- **Endpoint:** `/api/{stock_id}/{option}`
- **Description:** Returns the value and signal for a specific indicator (`option` = rsi, macd, bb, cmf) for a given stock (must end with `.NS`).
- **Query Parameters:**
  - `interval` (string, optional)
  - `period` (int, optional)
  - `window` (int, optional)
  - `num_std` (float, optional)
- **Response Example:**
```json
{
  "rsi": 65.95,
  "rsi_smooth": 65.2,
}
```

---

## Market Intel Engine Endpoints

### 1. Health Check
- **Method:** GET
- **Endpoint:** `/health` (on Market Intel Service port 8000)
- **Description:** Returns the health status of the Market Intel service.

### 2. Chat / Analysis
- **Method:** POST
- **Endpoint:** `/chat`
- **Description:** Submits a prompt to the AI engine for sentiment analysis.
- **Request Body:**
```json
{
  "prompt": "Analyze the sentiment for RELIANCE.NS..."
}
```
- **Response Example:**
```json
{
  "result": "{...JSON analysis...}",
  "timestamp": "2024-06-01T12:00:00Z"
}
```

---

## Controller Endpoints

### 1. Health Check (Admin)
- **Method:** GET
- **Endpoint:** `/api/admin/health`
- **Description:** Returns the health status of the controller service. Requires API key.
- **Response Example:**
```json
{
  "status": "OK",
  "timestamp": "2024-06-01T12:00:00Z"
}
```

---

### 2. Trigger Stock Analysis Cronjob
- **Method:** POST
- **Endpoint:** `/api/admin/trigger-cron`
- **Description:** Triggers the stock analysis cronjob manually. Requires API key.
- **Headers:**
  - `X-API-Key`: your-api-key
- **Response Example:**
```json
{
  "job": "stock-analysis",
  "status": "triggered",
  "message": "Job triggered successfully"
}
```

---

### 3. Trigger Kubernetes CronJob
- **Method:** GET
- **Endpoint:** `/api/admin/trigger-cron`
- **Description:** Triggers the Kubernetes cronjob for stock analysis. Requires API key.
- **Headers:**
  - `X-API-KEY`: your-api-key
- **Response Example (Success):**
```json
{
  "status": "success",
  "message": "Job created successfully from cronjob",
  "job_name": "sf-cron-api-1717261234-5678",
  "details": "Job sf-cron-api-1717261234-5678 created in namespace default"
}
```
- **Response Example (Error):**
```json
{
  "status": "error",
  "detail": "signal-check-cronjob not found in the cluster"
}
```

---

### 4. Maintenance Mode Status
- **Method:** GET
- **Endpoint:** `/api/admin/maintenance/status`
- **Description:** Checks if the system is currently in maintenance mode.
- **Response Example:**
```json
{
  "status": "off",
  "timestamp": "2024-06-01T12:00:00Z"
}
```

### 5. Toggle Maintenance Mode
- **Method:** GET
- **Endpoint:** `/api/admin/maintenance/{status}`
- **Description:** Enables (`on`) or disables (`off`) maintenance mode. Requires API key.
- **Path Parameters:**
  - `status`: "on" or "off"
- **Headers:**
  - `X-API-Key`: your-api-key
- **Response Example:**
```json
{
  "status": "on",
  "timestamp": "2024-06-01T12:00:00Z"
}
```

---

**Note:** Replace `{stock_id}` with the actual stock symbol (e.g., `RELIANCE.NS`).

For more details, see the main project README or contact the StockFlow team. 