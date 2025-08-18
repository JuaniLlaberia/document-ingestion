import logging
import os
import json
import hashlib
from io import BytesIO
from pathlib import Path
from typing import Tuple, List
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat, DocumentStream
from docling_core.types.doc import PictureItem
from src.models.documents import ImageData
from src.models.output import ImageOutput
from src.utils.prompts import GENERATE_IMG_DESCRIPTION_PROMPT, GENERATE_IMG_DESCRIPTION_SYSTEM
from src.llm.init import OllamaGenerator

class DocumentProcessor:
    def __init__(self, local_storage_path: str, img_scale: float):
        self.image_scale = img_scale
        self.local_storage_path = Path(local_storage_path)

        self.local_storage_path.mkdir(parents=True, exist_ok=True)

    def _extract_content(self, file_bytes: bytes, file_name: str) -> Tuple[str, List[ImageData]]:
        """
        Extracts text and images from file bytes

        Args:
            file_bytes (bytes): Document to extract file bytes
            file_name (str): File name

        Returns:
            text_content (str): Text content extracted from the file
            images (List[ImageData]): List of tuples containing the image path and the image bytes
        """
        logging.info(f"Extracting content for document {file_name}")

        pipeline_options = PdfPipelineOptions()
        pipeline_options.images_scale = self.image_scale
        pipeline_options.generate_page_images = True
        pipeline_options.generate_picture_images = True

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )

        file_bytes_buf = BytesIO(file_bytes)
        source = DocumentStream(name=file_name, stream=file_bytes_buf)
        result = converter.convert(source=source)

        text_content = result.document.export_to_markdown()
        processed_images = self._process_images(pictures=result.document.pictures, source_filename=file_name)

        return text_content, processed_images

    def _process_images(self, pictures: List[PictureItem], source_filename: str) -> List[ImageData]:
        """
        Proccess raw images objects into ImageData objects

        Args:
            pictures (List[PictureItem]): List of pictures extracted from document in docling type
            source_filename (str): Document filename

        Returns:
            processed_images (List[ImageData]): List of processed images with the ImageData type
        """
        processed_images = []

        for idx, picture in enumerate(pictures):
            image_bytes = self._pil_to_bytes(pil_image=picture.image.pil_image, format="PNG")
            image_id = self._generate_image_id(source_filename=source_filename,
                                               index=idx,
                                               image_content=image_bytes)

            image_data = ImageData(
                image_id=image_id,
                image_bytes=image_bytes,
                filename=f"{image_id}.png",
                format="PNG"
            )
            processed_images.append(image_data)

        return processed_images

    def _generate_image_id(self, source_filename: str, index: int, image_content: bytes) -> str:
        """
        Generate unique id for image based on source and content

        Args:
            source_filename (str): Document filename
            index (int): Image index in the process_images loop
            image_content (bytes): Image as bytes

        Returns:
            image_id (str): Unique id based on source and content
        """
        content_hash = hashlib.md5(image_content).hexdigest()[:8]
        base_name = Path(source_filename).stem

        return f"{base_name}_img_{index:03d}_{content_hash}"

    def _pil_to_bytes(self, pil_image, format='PNG') -> bytes:
        """
        Convert PIL Image to bytes
        """
        if pil_image is None:
            return b""

        byte_buffer = BytesIO()
        pil_image.save(byte_buffer, format=format)
        return byte_buffer.getvalue()

    def _store_images(self, images: List[ImageData]) -> List[ImageData]:
        """
        Stores images in 'Fake' bucket inside the ChromaDB repo (locally)

        Args:
            images (List[ImageData]): The list of images objects to store

        Returns:
            images (List[ImageData]): Updated list of images, each containing storage path
        """
        logging.info(f"Storing {len(images)} in {self.local_storage_path} bucket")

        for image in images:
            self.local_storage_path.mkdir(exist_ok=True)

            image_path = self.local_storage_path / image.filename

            with open(image_path, "wb") as f:
                f.write(image.image_bytes)

            image.path = image_path

        logging.info(f"All images were saved successfully")
        return images

    def _generate_img_descriptions(self, images: List[ImageData]) -> List[ImageData]:
        """
        Geneartes a description for each image and stores it in each image object

        Args:
            images (List[ImageData]): The list of images objects to store

        Returns:
            images (List[ImageData]): Updated list of images, each containing storage path
        """
        logging.info(f"Generating descriptions for {len(images)} images")

        for image in images:
            try:
                formatted_prompt = GENERATE_IMG_DESCRIPTION_PROMPT

                llm = OllamaGenerator(base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"), default_model=os.getenv("OLLAMA_LLM_MODEL", ""))

                response = llm.generate(prompt=formatted_prompt,
                                        system=GENERATE_IMG_DESCRIPTION_SYSTEM,
                                        response_format=ImageOutput,
                                        images=[image.image_bytes])

                parsed_response = json.loads(response["response"])
                image.description = parsed_response["description"]

            except Exception as e:
                logging.error(f"Failed to generate description for {image.image_id}: {e}")

        logging.info("All images description were generated")
        return images

    def run(self, file_bytes: bytes, file_name: str) -> Tuple[str, List[ImageData]]:
        """
        Run document processor pipeline

        Args
        """
        logging.info("Starting document processing pipeline")
        # 1. Extract content and raw images from document bytes
        text_content, images = self._extract_content(file_bytes=file_bytes, file_name=file_name)
        # 2. Store images in "local" bucket
        images = self._store_images(images=images)
        # 3. Generate descriptions for each image
        images = self._generate_img_descriptions(images=images)

        return text_content, images