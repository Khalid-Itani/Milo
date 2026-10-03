"""Only the documented session-token boundary; no BMI or guessed result API."""
from datetime import datetime, timezone
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException
from pydantic import BaseModel, AwareDatetime, Field, ValidationError
from app.config import settings

class SessionToken(BaseModel):
    session_token: str = Field(min_length=1, max_length=8192)
    expires_at: AwareDatetime

def mint_session():
    if not settings.visualize_secret_key:
        raise HTTPException(503, "visualize_not_configured")
    base = settings.visualize_api_base_url.rstrip("/")
    url = urlparse(base)
    if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
        raise HTTPException(503, "visualize_configuration_invalid")
    try:
        with httpx.Client(timeout=httpx.Timeout(10, connect=5), follow_redirects=False) as client:
            response = client.post(base+"/v1/sessions",
                headers={"Authorization": "Bearer "+settings.visualize_secret_key, "Content-Type": "application/json"},
                json={"host_user_ref": settings.visualize_host_user_ref})
            response.raise_for_status()
            result = SessionToken.model_validate(response.json())
            if result.expires_at <= datetime.now(timezone.utc):
                raise ValueError()
            return result.model_dump(mode="json")
    except httpx.TimeoutException:
        raise HTTPException(504, "visualize_timeout") from None
    except (httpx.HTTPError, ValidationError, ValueError, TypeError):
        raise HTTPException(502, "visualize_upstream_error") from None
