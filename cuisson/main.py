from typing import Optional
import logging
from fastapi import FastAPI
import model
logger = logging.getLogger(__name__)
app = FastAPI()


@app.get("/")
def read_root():
    return {"py-kitchen": "test test"}


@app.get("/users/")
def list_user():
    logger.info(model.get_users())
    return {}
