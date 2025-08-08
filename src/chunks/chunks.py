import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Chunker:
    def __init__(self, chunk_size: int, chunk_overlap: int):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter: RecursiveCharacterTextSplitter = None

    def run(self, doc_content: str) -> List[str]:
        """
        Splits document content into chunks

        Args:
            doc_content: str -> Document content as a string
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        logging.info(f"Starting document splitter process ({len(doc_content)} characters)...")
        chunks = self.text_splitter.split_text(doc_content)
        logging.info(f"Document was split successfully into {len(chunks)} chunks")

        return chunks