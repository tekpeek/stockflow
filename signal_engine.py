from fastapi import FastAPI
import signal_functions as sf

signal_engine = FastAPI()

@signal_engine.get("/{stock_id}")
def get_stock_data(stock_id: str):
    if stock_id.endswith(".NS"):
        return_data = sf.calculate_final_signal(stock_id)
        return return_data
    else:
        return {"error": "Incorrect Stock ID. Stock ID must end with .NS"}