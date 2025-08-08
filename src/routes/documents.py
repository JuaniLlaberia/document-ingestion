import os
import logging
from flask import Blueprint, request, jsonify
from src.chunks.chunks import Chunker
from src.utils.extract_doc_content import extract_doc_content
from src.chromadb.client import ChromaDBClient

documents_bp = Blueprint("documents", __name__)

ALLOWED_FILED = (".pdf", ".csv", ".docx", ".txt")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 800))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 100))

@documents_bp.route("/", methods=["POST"])
def ingest_document():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    _, extension = os.path.splitext(file.filename)

    if extension not in ALLOWED_FILED:
        return jsonify({"error": "File type is not supported",
                        "supported_files": list(ALLOWED_FILED)}), 400

    try:
        file_bytes = file.stream.read()
        doc_content = extract_doc_content(file_bytes=file_bytes, extension=extension)

        chunker = Chunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        chunks = chunker.run(doc_content=doc_content)

        client = ChromaDBClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", 8000))
        )

        collection_name = "documents"
        client.ingest_chunks(chunks=chunks, collection_name=collection_name)

        return jsonify({"message": f"Successfully added {len(chunks)} chunks to {collection_name} collection"}), 200

    except Exception as e:
        logging.error(f"Something went wrong: {e}")
        return jsonify({"error": "Something went wrong", "detail": e}), 500