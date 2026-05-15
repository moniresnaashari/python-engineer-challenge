from sqlmodel import Field
from sqlmodel import SQLModel


class Recipe(SQLModel, table=True):
    __tablename__ = "recipes"

    id: int | None = Field(default=None, primary_key=True)

    title: str
    ingredients: str
    instructions: str