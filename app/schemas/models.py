from pydantic  import BaseModel,EmailStr,constr

from pydantic import BaseModel, EmailStr, Field

class user_schema(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=255
    )
class login_schema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class document_schema(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1, max_length=500)
    uploaded_by: int = Field(gt=0)