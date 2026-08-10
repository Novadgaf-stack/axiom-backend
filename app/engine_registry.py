"""
Holds a reference to the running TradingEngine so API routes (registered at
import time) can reach it at call time, after it's created in the lifespan
startup handler. Avoids the ordering bug of trying to add routes to an
APIRouter after it's already been included into the FastAPI app.
"""
engine = None


def set_engine(instance):
    global engine
    engine = instance
