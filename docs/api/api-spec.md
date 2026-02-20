# API Specification

This document provides a technical reference for all microservice endpoints within the StockFlow ecosystem.

---

## 1. Signal Engine API
**Base URL**: `https://tekpeek.duckdns.org` (Internal: Port 8000)

### Get Final Signal
Returns the BharatQuant v4 recommendation for a specified stock.
- **Endpoint**: `/api/{stock_id}`
- **Method**: `GET`
- **Params**:
    - `stock_id`: (Required) Ticker symbol ending in `.NS` (e.g., `RELIANCE.NS`).
    - `interval`: (Optional) Analysis interval (default: `1d`).
- **Response**:
    ```json
    {
      "recommendation": "BUY",
      "buy": true,
      "score": 7,
      "strength": "Institutional (Unicorn)",
      "reason": "Hourly Higher Low confirmed... Bullish RSI Divergence detected",
      "entry_price": 2540.5,
      "take_profit": 2610.2,
      "stop_loss": 2480.0
    }
    ```

---

## 2. StockFlow Controller (Admin)
**Base URL**: `https://tekpeek.duckdns.org/default` (Internal: Port 9000)
**Auth**: Requires `X-API-Key` header.

### Toggle Maintenance Mode
- **Endpoint**: `/api/admin/maintenance/{status}`
- **Method**: `GET`
- **Path Params**: `status` (on/off)

### Update Discovery Tickers
- **Endpoint**: `/api/admin/top-stocks`
- **Method**: `POST`
- **Body**: `{"tickers": ["AAPL.NS", "GOOG.NS"]}`

---

## 3. Market Intel Engine
**Internal Port**: 8000 (Accessed via Controller/Orchestrator)

### AI Sentiment Analysis
- **Endpoint**: `/chat`
- **Method**: `POST`
- **Body**: `{"prompt": "Analyze these stocks..."}`
- **Response**: JSON object containing sentiment scores and analysis strings.

---

## Health Check Contract
All services implement a standard health check endpoint used by the resilience mesh.

| Service | Endpoint | Success Response |
|---------|----------|------------------|
| Signal Engine | `/api/health` | `{"status": "OK"}` |
| Controller | `/api/admin/health` | `{"status": "OK"}` |
| Market Intel | `/health` | `{"status": "OK"}` |
