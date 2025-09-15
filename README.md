# refire

A flexible Python decorator for retrying functions upon failure with support for exponential backoff, jitter, and configurable retry policies.

## Features

- Retry functions automatically when exceptions occur.
- Configurable number of retries or infinite retries.
- Adjustable initial delay and exponential backoff.
- Optional maximum delay to cap wait times.
- Support for random jitter to prevent retry storms (thundering herd problem).
- Specify which exception types trigger retries.

## Installation

Install via pip:

```bash
pip install refire
# or
uv add refire
```

Or clone the repository:

```bash
git clone https://github.com/maxscheijen/refire.git
cd refire
pip install .
# or
uv sync
```

## Usage

### Basic Example

```python
import random

from refire import refire


@refire(tries=5, delay=2, backoff=2, jitter=(0, 1))
def flaky_function():
    if random.random() < 0.7:
        raise ValueError("Unlucky!")
    return "Success!"

result = flaky_function()
print(result)  # "Success!" after several retries
```

### Custom Exception

```python
class CustomError(Exception):
    pass

@refire(exceptions=CustomError, tries=3, delay=1)
def risky_function():
    raise CustomError("Oops!")

risky_function()
```

## Logging

Retries are by default logged at WARNING level:

```
Caught ValueError: Unlucky!. Retrying in 2.00s (remaining=4)
```

## Development

This project uses [uv](https://docs.astral.sh/uv/). To set up a local development environment:

```bash
# Clone the repository
git clone https://github.com/maxscheijen/refire.git
cd refire

# Install dependencies (using uv)
uv sync --extra dev

# Or using pip
pip install -e ".[dev]"
```

### Tests

This project uses [pytest](https://docs.pytest.org/):

```bash
pytest
```
