from pydantic import BaseModel, Field

class ImageOutput(BaseModel):
    description: str = Field(..., description="Paragraph describing the image")