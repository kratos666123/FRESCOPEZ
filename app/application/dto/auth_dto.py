from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, examples=["admin_user"])
    password: str = Field(..., min_length=6, max_length=128, examples=["securePassword123"])

    model_config = {"str_strip_whitespace": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class TokenPayload(BaseModel):
    sub: int          # user_id
    username: str
    role: str
    type: str         # "access" or "refresh"
    exp: int
