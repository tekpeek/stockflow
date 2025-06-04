FROM ubuntu:latest
RUN apt-get update && apt-get install python3 python3-pip python3-venv -y
WORKDIR /app
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
RUN pip install fastapi uvicorn yfinance pandas
COPY signal_engine.py /app/signal_engine.py
COPY signal_functions.py /app/signal_functions.py
CMD ["uvicorn", "signal_engine:signal_engine", "--host", "0.0.0.0", "--port", "8000", "--reload"]