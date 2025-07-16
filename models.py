from pydantic import BaseModel


class Technology(BaseModel):
    language: str
    version: str
    package_manager: str


class SuccessfulBlueprint(BaseModel):
    success: bool
    message: str
