import os
import chromadb
import logging
from uuid import uuid4
from typing import List
from chromadb.utils.embedding_functions.ollama_embedding_function import OllamaEmbeddingFunction

class ChromaDBClient:
    def __init__(self, host: str, port: int):
        self.client = chromadb.HttpClient(host=host, port=port)
        self.embedding_fn = OllamaEmbeddingFunction(
            url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model_name=os.getenv("OLLAMA_MODEL", "jina/jina-embeddings-v2-base-en:latest")
        )

    def ingest_chunks(self, chunks: List[str], collection_name: str):
        """
        Gets provided collection from ChromaDB and adds documents

        Args:
            chunks: List[str] -> The list of chunks to add to the DB
            collection_name: str -> Name of the collection we are adding the chunks to
        """
        try:
            logging.info(f"Getting collection: '{collection_name}'")
            collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )

            logging.info(f"Adding {len(chunks)} documents to '{collection_name}' collection")
            collection.add(
                ids=[str(uuid4()) for _ in chunks],
                documents=chunks,
                # metadatas=[]
            )

            logging.info(f"Successfully added {len(chunks)} documents")
        except Exception as e:
            logging.error(f"Failed to ingest chunks: {e}")
            raise e