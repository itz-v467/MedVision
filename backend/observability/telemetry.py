import logging
from functools import wraps
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def trace_ai_decision(engine_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"[TRACE] Starting AI decision via {engine_name}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"[TRACE] Completed AI decision via {engine_name} in {duration:.3f}s. Result: Success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"[TRACE] Failed AI decision via {engine_name} in {duration:.3f}s. Error: {str(e)}")
                raise e
        return wrapper
    return decorator
