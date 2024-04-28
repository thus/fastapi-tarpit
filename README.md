# FastAPI Tarpit

[FastAPI](https://fastapi.tiangolo.com/) middleware that purposely delays
incoming connections on unused routes.

Definition of a tarpit from [Wikipedia](https://en.wikipedia.org/wiki/Tarpit_(networking)):

> A tarpit is a service on a computer system (usually a server) that purposely delays incoming connections. The technique was developed as a defense against a computer worm, and the idea is that network abuses such as spamming or broad scanning are less effective, and therefore less attractive, if they take too long. The concept is analogous with a tar pit, in which animals can get bogged down and slowly sink under the surface, like in a swamp.

## Installation

Install the package using pip:

```bash
pip install fastapi-tarpit
```

## Usage

```python
from fastapi import FastAPI
from fastapi_tarpit import HTTPTarpitMiddleware

app = FastAPI()

app.add_middleware(HTTPTarpitMiddleware)

@app.get("/foo")
async def foobar():
    return {"foo": "bar"}
```

The code above triggers the tarpit on any other routes than `/foo`, and
routes related to docs.
