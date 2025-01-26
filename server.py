from fastapi import FastAPI, Response
import logging

logging.getLogger('matplotlib').setLevel(logging.WARNING)

app = FastAPI()

message_file = "data/message.json"

import json


@app.get("/token_official_message")
async def token_official_message():
    with open(message_file, 'r', encoding='utf8') as fcc_file:
        message = json.load(fcc_file)
    return message


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8088)
