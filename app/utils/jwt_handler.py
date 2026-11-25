from typing import Any
from dotenv import load_dotenv
import os
from jose import jwt, JWTError
from datetime import datetime, timedelta , timezone

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY") 
ALGORITHM  = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

def create_access_token(data: dict):

    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY, # type: ignore
        algorithm=ALGORITHM # type: ignore
    )
def verify_token(token: str):

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY, # type: ignore
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None