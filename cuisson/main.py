from typing import Optional
import logging
from fastapi import FastAPI
logger = logging.getLogger(__name__)
app = FastAPI()


@app.get("/")
def read_root():
    return {"py-kitchen": "test"}


@app.post("/triggers/user_update/")
def user_update(update: dict):
    logger.info(update)
    return {'status': 'ok'}
