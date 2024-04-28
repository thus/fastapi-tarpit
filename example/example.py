import logging

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from fastapi_tarpit import HTTPTarpitMiddleware

logging.basicConfig(encoding='utf-8', level=logging.INFO)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(HTTPTarpitMiddleware)


# Tell web scrapers and robots to stay away!
@app.get("/robots.txt", response_class=PlainTextResponse)
def robots():
    return """User-agent: *\nDisallow: /"""
