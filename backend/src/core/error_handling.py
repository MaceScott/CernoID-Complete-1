from typing import Type, Callable
from functools import wraps

def handle_exceptions(
    *exception_types: Type[Exception],
    logger: Callable = print,
    reraise: bool = False
):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                logger(f"Error in {func.__name__}: {str(e)}")
                if reraise:
                    raise
        return wrapper
    return decorator

# Usage example:
@handle_exceptions(ValueError, TypeError, logger=custom_logger.error)
def process_image(image_path: str):
    # Processing logic here
    pass 