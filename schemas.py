from pydantic import BaseModel


class PostCreate(BaseModel):
    content: str

class PostOut(BaseModel):
    post_id: int
    content: str
    user_id: int

    class Config:
        orm_mode = True