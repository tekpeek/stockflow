# StockFlow: Core Architecture & Ecosystem

StockFlow is an event-driven microservice ecosystem designed for real-time stock analysis and automated signal alerts. It follows a "Resilience Mesh" pattern, where independent services monitor and recovery each other through health-checks and snapshotting.

## System Context Diagram

The following diagram illustrates how StockFlow interacts with external systems within its ecosystem.

## System Workflows

The StockFlow ecosystem is organized into three distinct operational flows.

### 1. Market Scanning & Discovery
A morning process to identify the day's high-volume "stock universe."

```mermaid
graph LR
    DC[Discovery CronJob] --> |Scan & Sort 900| SC[Controller API]
    SC --> |Push to ConfigMap| CM[(top-stocks-cm ConfigMap)]
```

### 2. Daily Analysis Orchestration
The core processing pipeline showing the central role of the Signal-Check orchestrator.

```mermaid
graph TD
    CM[(top-stocks-cm ConfigMap)] --> |Read Tickers| SCC[Signal-Check CronJob]
    
    SCC --> |1. Technical Request| SE[Signal Engine]
    SE --> |2. Math Results| SCC
    
    SCC --> |3. Sentiment Request| MIE[Market Intel]
    MIE --> |4. AI JSON Data| SCC
    
    SCC --> |5. Final Results| ED[Event Dispatcher]
    ED --> |6. Email| Email((Trader Inbox))
```

### 3. Health Check & Resilience
Automated monitoring with conditional alerting logic.

```mermaid
graph TD
    HC[Health Check CronJob] --> |Probe 1| SE[Signal Engine]
    HC --> |Probe 2| SC[Controller API]
    HC --> |Probe 3| MIE[Market Intel]
    
    Engines{Service Healthy?}
    SE & SC & MIE --> Engines
    
    Engines -- No --> ED[Event Dispatcher]
    ED --> |Health Alert| Email((Operator Inbox))
    
    Engines -- Yes --> End[No Action]
```

## Core Components

### 1. Daily Analysis Pipeline
- **Discovery**: A morning CronJob that filters the market for the top 900 high-volume stocks.
- **Controller**: Manages the persistence of results into Kubernetes ConfigMaps.
- **Signal-Check**: The main orchestrator that performs math (Signal Engine) and AI (Market Intel) verification.
- **Event Dispatcher**: The dedicated notification engine for sending emails.

### 2. Microservices
- **Signal Engine**: Handles technical indicator calculations (RSI, BharatQuant v4).
- **Market Intel**: Performs LLM-based sentiment analysis on filtered stocks.

## Resilience & Maintenance
- **Health Checks**: A dedicated CronJob monitors all microservices. If any service is unresponsive, it triggers an alert via the **Event Dispatcher**.
- **Maintenance Mode**: A public-facing API on the **Controller** allows toggling maintenance mode for the **Signal Engine**, pausing analysis logic without disrupting service uptime.
