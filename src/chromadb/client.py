import os
import chromadb
import logging
from uuid import uuid4
from typing import List, Optional, Union, Dict, Any
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

logging.getLogger("chromadb.utils.embedding_functions.ollama_embedding_function").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

class ChromaDBClient:
    def __init__(self, host: str, port: int):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.embedding_fn = OllamaEmbeddingFunction(
            url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model_name=os.getenv("OLLAMA_MODEL", "jina/jina-embeddings-v2-base-en:latest")
        )

    def ingest_chunks(self,
                    chunks: List[str],
                    collection_name: str,
                    metadatas: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None,
                    embedding_type: str = "text",
                    image_urls: Optional[List[str]] = None):
        """
        Gets provided collection from ChromaDB and adds documents

        Args:
            chunks (List[str]): The list of chunks to add to the DB
            collection_name (str): Name of the collection we are adding the chunks to
            metadatas (Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]):
                - If List: Each dict corresponds to metadata for each chunk
                - If Dict: Same metadata applied to all chunks
                - If None: Default metadata with embedding_type will be applied
            embedding_type (str): Type of embedding ("text", "image", etc.)
            image_urls (Optional[List[str]]): List of image URLs
        """
        try:
            logging.info(f"Getting collection: '{collection_name}'")
            collection = self.client.get_collection(
                name=collection_name,
                # embedding_function=self.embedding_fn # Commented because we are generating the embeddings outside chromadb
            )

            num_chunks = len(chunks)
            final_metadatas = []

            if image_urls is not None:
                embedding_type = "image"

            if metadatas is None:
                for i in range(num_chunks):
                    metadata = {"embedding_type": embedding_type}
                    if image_urls:
                        metadata["image_url"] = image_urls[i]

                    final_metadatas.append(metadata)
            elif isinstance(metadatas, dict):
                for i in range(num_chunks):
                    metadata = metadatas.copy()
                    metadata["embedding_type"] = embedding_type

                    if image_urls:
                        metadata["image_url"] = image_urls[i]

                    final_metadatas.append(metadata)
            elif isinstance(metadatas, list):
                if len(metadatas) != num_chunks:
                    raise ValueError(f"Number of metadata items ({len(metadatas)}) must match number of chunks ({num_chunks})")

                for i, metadata in enumerate(metadatas):
                    if not isinstance(metadata, dict):
                        raise ValueError("Each metadata item must be a dictionary")

                    final_metadata = metadata.copy()
                    final_metadata["embedding_type"] = embedding_type

                    if image_urls:
                        final_metadata["image_url"] = image_urls[i]

                    final_metadatas.append(final_metadata)
            else:
                raise ValueError("metadatas must be None, a dict, or a list of dicts")

            embeddings = [self.embedding_fn([chunk])[0] for chunk in chunks]

            logging.info(f"Adding {len(chunks)} documents to '{collection_name}' collection")
            collection.add(
                ids=[str(uuid4()) for _ in chunks],
                embeddings=embeddings,
                documents=chunks,
                metadatas=final_metadatas
            )

            logging.info(f"Successfully added {len(chunks)} documents")
        except Exception as e:
            logging.error(f"Failed to ingest chunks: {e}")
            raise e