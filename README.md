# StockFlow - Real-Time Stock Signal Analysis Microservice

StockFlow is an automated stock analysis platform developed to enhance the efficiency of identifying potential trading opportunities. Designed to replicate and automate the analytical methods and indicators I typically employ, StockFlow systematically evaluates a broad range of stocks and generates a curated shortlist of candidates warranting further review.

## Why was it built ?
This tool is intended to serve as an initial screening layer for me, providing structured assistance in narrowing down the universe of stocks to those with promising characteristics. It is not a definitive prediction system to be relied upon blindly but rather a time-saving aid that supports more focused and informed decision-making. By automating the preliminary stages of analysis, StockFlow significantly reduces the effort and time required by me to identify high-potential stocks for further evaluation.

## Who is it for ?
Anyone who wants to trim down potential stocks to a limited count so that they can invest less time in initial screening and focus on more deeper analysis.

## Features

### **Signal Engine**
- **Multi-Indicator Analysis**: Identifying potential entry points by combining signals from RSI, MACD, Bollinger Bands, CMF (Chaikin Money Flow)
- **Real-time Data**: Live stock data from Yahoo Finance
- **Confidence Scoring**: Signal strength assessment (Weak/Strong)

### **Technical Indicators**
- **RSI (Relative Strength Index)**: Momentum oscillator with smoothing
- **MACD (Moving Average Convergence Divergence)**: Trend and momentum analysis
- **Bollinger Bands**: Volatility and price channel analysis
- **CMF (Chaikin Money Flow)**: Volume-weighted price analysis

### **API Services**
- **Signal Engine API**: Real-time stock analysis endpoints
- **Controller API**: Administrative and cronjob management
- **CORS Support**: Cross-origin request handling
- **Error Handling**: Comprehensive error responses
- **Authentication for selected APIs**: API Key Authentication for administrative and sensitive endpoints 

### **Automation & Monitoring**
- **Scheduled Analysis**: Automated cronjobs for regular stock screening
- **Email Notifications**: Email alert with potential stocks during scheduled analysis
- **Health Monitoring**: Automated system health check and status monitoring with email alert on failure

### **Deployment & Infrastructure**
- **Lightweight Kubernetes**: Full K3s deployment with Role based access control
- **Docker Containerization**: Microservice architecture
- **Traefik Ingress**: Provides routing with TLS encryption, and configures CORS to allow cross-service API calls securely.
- **ConfigMaps & Secrets**: Secure configuration management with kubernetes secrets and configmaps
- **CI/CD Pipeline with Automated Deployment**: Automated deployment using Github Actions to k3s cluster
- **Cloud VM for complete deployment**: The entire service runs on Oracle Cloud Infrastructure VM which acts as a self hosted runner as well, on Github Actions.
- **Static Frontend**: Static Frontend for stockflow APIs using Bootstrap, CSS, Javascript.

## 🏗️ Architecture

### **Microservices**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Signal Engine │    │ StockFlow        │    │   CronJobs      │
│   (Port: 8000)  │    │ Controller       │    │   (Automated)   │
│                 │    │ (Port: 9000)     │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Traefik       │
                    │   Ingress       │
                    └─────────────────┘
```

### **Data Flow**
1. **User Request** → Signal Engine API
2. **Data Fetch** → Yahoo Finance (yfinance)
3. **Analysis** → Technical Indicators
4. **Signal Generation** → Aggregation Algorithm
5. **Response** → Formatted JSON with buy/sell signals

## 📊 Technical Indicators

### **RSI (Relative Strength Index)**
- **Purpose**: Momentum oscillator measuring speed and magnitude of price changes
- **Calculation**: Wilder's smoothing with EMA
- **Signals**: 
  - Oversold: RSI < 30
  - Neutral: 40 ≤ RSI ≤ 70
  - Overbought: RSI > 70

### **MACD (Moving Average Convergence Divergence)**
- **Purpose**: Trend-following momentum indicator
- **Components**: MACD line, Signal line, Histogram
- **Signals**: Bullish crossover, momentum analysis, trend strength

### **Bollinger Bands**
- **Purpose**: Volatility indicator and price channel
- **Components**: Upper band, Middle band (SMA), Lower band
- **Signals**: Price squeeze, oversold conditions, breakout detection

### **CMF (Chaikin Money Flow)**
- **Purpose**: Volume-weighted price analysis
- **Range**: -1 to +1
- **Signals**: Money flow confirmation, volume analysis

## 🔧 API Endpoints

### **Signal Engine API** (`/api/signal-engine`)

#### **Full Analysis**
```http
GET /{stock_id}?interval={interval}
```
- **Parameters**: 
  - `stock_id`: Stock symbol (e.g., RELIANCE.NS)
  - `interval`: Time interval (1d, 1wk, 1mo)
- **Response**: Complete analysis with all indicators

#### **Individual Indicators**
```http
GET /{stock_id}/{indicator}?interval={interval}
```
- **Indicators**: `rsi`, `macd`, `bollinger`, `sma`, `ema`
- **Response**: Specific indicator analysis

### **Controller API** (`/api/controller`)

#### **Health Check**
```http
GET /admin/health
```
- **Response**: System status and timestamp

#### **Manual Cronjob Trigger**
```http
GET /admin/trigger-cron
```
- **Headers**: `X-API-Key: {api_key}`
- **Response**: Cronjob execution status

## 🚀 Deployment

### **Prerequisites**
- Kubernetes cluster (K3s/RKE2)
- kubectl configured
- Docker registry access
- SMTP credentials (for email notifications)

### **Environment Variables**
```bash
# SMTP Configuration
SMTP_PASSWORD=your_smtp_password
SMTP_USER=noreply.avinash.s@gmail.com
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com

# API Security
SF_API_KEY=your_api_key

# Strategy Configuration
INTERVAL=1d
PERIOD=14
WINDOW=20
NUM_STD=2
```

### **Deployment Steps**
1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd stockflow
   ```

2. **Set Environment Variables**
   ```bash
   export SMTP_PASSWORD="your_password"
   export SF_API_KEY="your_api_key"
   ```

3. **Deploy to Kubernetes**
   ```bash
   chmod +x deploy_project.sh
   ./deploy_project.sh
   ```

### **Deployment Components**
- **Signal Engine**: Main analysis service
- **StockFlow Controller**: Administrative service
- **CronJobs**: Automated stock screening
- **Services**: Load balancers and ingress
- **RBAC**: Role-based access control
- **ConfigMaps**: Configuration management
- **Secrets**: Sensitive data storage

## 📈 Signal Generation Logic

### **Signal Aggregator v3**
The latest signal aggregation algorithm combines multiple indicators:

1. **MACD + CMF**: MACD bullish with positive CMF
2. **MACD Momentum**: Positive histogram with bullish trend
3. **Bollinger Bands + Volume**: Price near lower band with volume confirmation
4. **Bollinger Crossover**: Price crossed above middle band

### **Buy Signal Conditions**
- **Strong Signal**: 3+ positive indicators
- **Weak Signal**: 2 positive indicators
- **No Signal**: <2 positive indicators

### **Signal Strength**
- **Strong**: Multiple confirming indicators
- **Weak**: Limited indicator confirmation

## 🔍 Monitoring & Health Checks

### **Health Check Cronjob**
- **Schedule**: Every 5 minutes
- **Purpose**: Monitor system health
- **Actions**: Log system status, trigger alerts

### **Signal Check Cronjob**
- **Schedule**: Daily at 9:00 AM IST
- **Purpose**: Analyze top 500 NSE stocks
- **Actions**: Generate signals, send email notifications

### **Email Notifications**
- **Trigger**: Significant signals detected
- **Content**: Stock list, signal details, confidence levels
- **Format**: HTML email with analysis summary

## 🛠️ Development

### **Local Development**
```bash
# Signal Engine
cd src/api
python signal_engine.py

# Controller
cd src/api
python stockflow_controller.py
```

### **Testing**
```bash
# Test API endpoints
curl http://localhost:8000/RELIANCE.NS
curl http://localhost:8000/RELIANCE.NS/rsi
```

### **Docker Build**
```bash
# Signal Engine
docker build -f dockerfiles/Dockerfile.signal-engine -t signal-engine .

# Controller
docker build -f dockerfiles/Dockerfile.stockflow-controller -t stockflow-controller .
```

## 📁 Project Structure
```
stockflow/
├── src/
│   ├── api/
│   │   ├── signal_engine.py          # Main API service
│   │   └── stockflow_controller.py   # Controller service
│   └── core/
│       ├── signal_functions.py       # Analysis algorithms
│       ├── cronjob-execution.py      # Automated analysis
│       ├── healthcheck-execution.py  # Health monitoring
│       ├── smtp_email_trigger.py     # Email notifications
│       └── top_500_nse_tickers.py    # Stock list
├── kubernetes/
│   ├── deployments/                  # K8s deployments
│   ├── services/                     # K8s services
│   ├── cronjobs/                     # K8s cronjobs
│   ├── configmaps/                   # K8s configmaps
│   ├── rbac/                         # K8s RBAC
│   └── middlewares/                  # K8s middlewares
├── dockerfiles/                      # Docker configurations
├── stock_data/                       # Data storage
├── backtest_directory/               # Backtesting results
└── deploy_project.sh                 # Deployment script
```

## 🔐 Security

### **API Authentication**
- **API Key**: Required for administrative endpoints
- **Headers**: `X-API-Key` for authentication
- **Scope**: Controller API endpoints only

### **Kubernetes Security**
- **RBAC**: Role-based access control
- **Service Accounts**: Dedicated accounts for services
- **Secrets**: Encrypted sensitive data storage
- **Network Policies**: Pod-to-pod communication control

## 📊 Performance

### **Optimizations**
- **Caching**: Technical indicator calculations
- **Async Processing**: Non-blocking API responses
- **Resource Limits**: Kubernetes resource constraints
- **Load Balancing**: Traefik ingress controller

### **Scalability**
- **Horizontal Scaling**: Multiple pod replicas
- **Auto-scaling**: Kubernetes HPA support
- **Resource Management**: CPU/Memory limits
- **Monitoring**: Prometheus metrics ready

## 🐛 Troubleshooting

### **Common Issues**
1. **CORS Errors**: Ensure CORS middleware is configured
2. **API Timeouts**: Check network connectivity and resource limits
3. **Data Fetch Errors**: Verify stock symbols and Yahoo Finance access
4. **Cronjob Failures**: Check Kubernetes cluster status and RBAC

### **Logs**
```bash
# Signal Engine logs
kubectl logs -f deployment/signal-engine

# Controller logs
kubectl logs -f deployment/stockflow-controller

# Cronjob logs
kubectl logs -f job/signal-check-manual
```

## 📞 Support

For issues and questions:
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check this README and inline code comments
- **Logs**: Review Kubernetes pod logs for debugging

## 📄 License

This project is proprietary software. All rights reserved.

---

**StockFlow** - Empowering intelligent stock trading decisions through advanced technical analysis.
