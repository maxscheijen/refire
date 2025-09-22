import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union


def refire(
    exceptions: Union[Type[BaseException], Tuple[Type[BaseException], ...]] = Exception,
    tries: Optional[int] = 3,
    delay: Union[int, float] = 1,
    max_delay: Optional[Union[int, float]] = None,
    backoff: Union[int, float] = 2,
    jitter: Union[int, Tuple[int, int]] = 0,
    log_level: int = logging.WARNING,
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable], Callable]:
    """Creates a decorator that retries a function upon failure.

    This decorator re-executes a function when specified exceptions are raised.
    It supports configurable retry attempts, delays, exponential backoff,
    jitter, and maximum wait time between retries.

    Args:
        exceptions (Union[Type[BaseException], Tuple[Type[BaseException], ...]], optional):
            Exception type(s) to catch. Defaults to `Exception`.
        tries (Optional[int], optional):
            Number of retry attempts. If `None`, retries indefinitely.
            Defaults to `3`.
        delay (Union[int, float], optional):
            Initial delay (in seconds) before the first retry. Defaults to 1.
        max_delay (Optional[float], optional):
            Maximum allowed delay between retries. If `None`, no maximum
            is enforced. Defaults to None.
        backoff (Union[int, float], optional):
            Multiplicative factor by which the delay increases after each
            failed attempt. For example, `backoff=2` doubles the delay each
            time. Defaults to 2.
        jitter (Union[int, float, Tuple[float, float]], optional):
            Random jitter added to the delay to prevent retry storms (thundering herd).
            - If a number, jitter is drawn uniformly from `[0, jitter]`.
            - If a tuple `(low, high)`, jitter is drawn uniformly from
              `[low, high]`.
            - If 0, no jitter is applied.
            Defaults to 0.1.
        log_level (Optional[int]):
            Logging level used when reporting retry attempts (e.g., `logging.WARNING`).
            Defaults to `logging.WARNING`.
        logger (Optional[logging.Logger]):
            Logger instance to use for logging retry messages. If `None`,
            falls back to a module-level logger (`logging.getLogger(__name__)`).
            Defaults to None.

    Returns:
        Callable[[Callable], Callable]:
            A decorator that applies the retry logic to the wrapped function.

    Raises:
        Exception: The last caught exception is re-raised if all retry
        attempts fail.

    Example:
        ```python
        @refire(tries=5, delay=2, backoff=2, jitter=(0, 1))
        def flaky_function():
            if random.random() < 0.7:
                raise ValueError("Unlucky!")
            return "Success!"

        flaky_function()
        "Success!"  # after several retries
        ```
    """

    log = logger or logging.getLogger(__name__)

    def _jitter() -> float:
        if isinstance(jitter, tuple):
            return random.uniform(*jitter)
        return random.uniform(0, float(jitter)) if jitter else 0.0

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            remaining_tries, current_delay = tries, delay

            while remaining_tries is None or remaining_tries != 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if remaining_tries is not None:
                        remaining_tries -= 1
                        if remaining_tries == 0:
                            raise

                    log.log(
                        log_level,
                        f"Caught {type(e).__name__}: {e}. "
                        f"Retrying in {current_delay:.2f}s "
                        f"(remaining={remaining_tries if remaining_tries is not None else '∞'})",
                    )

                    time.sleep(max(0, current_delay))

                    base_delay = current_delay * backoff
                    delay_with_jitter = base_delay + _jitter()
                    effective_max_delay = (
                        max_delay if max_delay is not None else float("inf")
                    )
                    current_delay = min(delay_with_jitter, effective_max_delay)

        return wrapper

    return decorator
