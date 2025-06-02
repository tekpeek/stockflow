import fastapi from FastAPI
import signal_functions as sf

signal_engine = FastAPI()

@signal_engine.get("/{stock_id}")
def get_stock_data(stock_id: str):
    if stock_id.endswith(".NS"):
        return_data = sf.calculate_final_signal(stock_id)
    else:
        return {"error": "Stock ID must end with .NS"}