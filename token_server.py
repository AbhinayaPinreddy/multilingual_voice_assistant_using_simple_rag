from fastapi import FastAPI
from livekit import api
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

API_KEY = os.getenv("LIVEKIT_API_KEY")
API_SECRET = os.getenv("LIVEKIT_API_SECRET")


@app.get("/get-token")
def get_token(identity: str = "user", room: str = "voice-room"):
    token = (
        api.AccessToken(API_KEY, API_SECRET)
        .with_identity(identity)
        .with_name(identity)
        .with_ttl(datetime.timedelta(hours=1))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room
            )
        )
    )

    return {"token": token.to_jwt()}