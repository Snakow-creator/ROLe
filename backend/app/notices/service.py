from pydantic import BaseModel, field_validator, Field

class WebNotice(BaseModel):
    title: str
    message: str
    seconds: int = Field(default=10, gt=0)

    @field_validator("seconds")
    @classmethod
    def validate_seconds(cls, v):
        if v < 0:
            raise ValueError("seconds must be non-negative")
        return v
