from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_complexity(cls, v):
        # Check password length
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # Check for uppercase
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')

        # Check for digit
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one number')

        return v

    @validator('email')
    def validate_email(cls, v):
        # This is a redundant check as pydantic's EmailStr already validates email format
        # But we keep it for clarity and additional validation if needed
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


class UserInDB(UserResponse):
    hashed_password: str