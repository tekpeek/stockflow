# Stock Signal Engine UI

A modern Bootstrap-based web interface for the Stock Signal Engine API.

## Features

- **Modern UI**: Clean, responsive Bootstrap 5 interface
- **Real-time Analysis**: Get stock analysis and trading signals
- **Multiple Analysis Types**: RSI, MACD, Bollinger Bands, SMA, EMA, and Full Analysis
- **Configurable Parameters**: Adjust interval, period, window, and standard deviations
- **Error Handling**: User-friendly error messages and loading states

## How to Use

1. **Start the API Server**:
   ```bash
   cd src/api
   python signal_engine.py
   ```

2. **Access the UI**:
   Open your browser and navigate to `http://localhost:8000`

3. **Enter Stock Information**:
   - **Stock ID**: Enter a stock symbol (must end with .NS, e.g., RELIANCE.NS)
   - **Analysis Type**: Choose between Full Analysis or individual indicators
   - **Parameters**: Adjust the technical analysis parameters as needed

4. **Get Results**:
   Click "Get Analysis" to retrieve real-time stock analysis data

## API Endpoints

The UI interacts with these API endpoints:

- `GET /{stock_id}` - Full analysis for a stock
- `GET /{stock_id}/{option}` - Individual indicator analysis (rsi, macd, bollinger, sma, ema)

## Parameters

- **Interval**: Time interval for data (1d, 1wk, 1mo)
- **Period**: Period for calculations (default: 14)
- **Window**: Window size for moving averages (default: 20)
- **Standard Deviations**: Number of standard deviations for Bollinger Bands (default: 2)

## Supported Stock Symbols

Currently supports Indian stocks with `.NS` suffix (NSE - National Stock Exchange).

## File Structure

```
src/api/
├── signal_engine.py      # FastAPI server
├── static/
│   └── index.html        # Bootstrap UI
└── README.md            # This file
```

## Dependencies

- FastAPI
- Uvicorn
- Bootstrap 5 (CDN)
- Bootstrap Icons (CDN)

## Troubleshooting

- Ensure the API server is running on port 8000
- Check that stock symbols end with `.NS`
- Verify network connectivity if using remote API
- Check browser console for any JavaScript errors 