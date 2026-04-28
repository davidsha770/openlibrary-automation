import asyncio
import functools
import logging

logger = logging.getLogger("automation")

def retry_on_failure(times=3, delay=2):
    """
    A decorator that retries an async function if it raises an exception.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(times):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed for '{func.__name__}': {e}")
                    if attempt < times - 1:
                        await asyncio.sleep(delay)
            
            logger.error(f"All {times} attempts failed for '{func.__name__}'.")
            raise last_exception
        return wrapper
    return decorator