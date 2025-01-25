from fastapi import FastAPI
import logging

logging.getLogger('matplotlib').setLevel(logging.WARNING)

app = FastAPI()


@app.get("/token_official_message")
async def token_official_message():
    print("hell world")


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8088)
