from fastapi import Header, HTTPException, status

from app.config import get_settings


async def validate_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != get_settings().api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing X-API-Key", headers={"WWW-Authenticate": "ApiKey"})
