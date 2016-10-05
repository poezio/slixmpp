"""
asyncio-related utilities
"""

import asyncio
from functools import wraps

def future_wrapper(func):
    """
    Make sure the result of a function call is an asyncio.Future()
    object.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, asyncio.Future):
            return result
        future = asyncio.Future()
        future.set_result(result)
        return future

    return wrapper
