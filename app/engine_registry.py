"""
Holds a reference to the running TradingEngine so API routes (registered at
import time) can reach it at call time, after it's created in the lifespan
startup handler. Avoids the ordering bug of trying to add routes to an
APIRouter after it's already been included into the FastAPI app.
"""
engine = None
engine_task = None
keep_alive_task = None
config_problems: list[str] = []


def set_engine(instance, task=None):
    global engine, engine_task
    engine = instance
    engine_task = task


def set_keep_alive_task(task):
    global keep_alive_task
    keep_alive_task = task


def set_config_problems(problems: list[str]):
    global config_problems
    config_problems = problems


def is_engine_task_alive() -> bool:
    return engine_task is not None and not engine_task.done()


def is_keep_alive_active() -> bool:
    return keep_alive_task is not None and not keep_alive_task.done()

