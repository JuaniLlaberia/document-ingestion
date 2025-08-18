from dataclasses import dataclass

@dataclass
class ImageData:
    image_id: str
    filename: str
    image_bytes: bytes
    format: str
    path: str = None
    description: str = None