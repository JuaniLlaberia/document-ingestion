import os
import logging
from flask import Blueprint, request, jsonify
from src.chunks.chunks import Chunker
from src.chromadb.client import ChromaDBClient
from src.documents.document_processor import DocumentProcessor

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

        document_processor = DocumentProcessor(local_storage_path=os.getenv("BUCKET_DIR", "bucket"), img_scale=2.0)
        text_content, images = document_processor.run(file_bytes=file_bytes, file_name=file.filename)

        chunker = Chunker(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
        content_chunks = chunker.run(doc_content=text_content)

        client = ChromaDBClient(
            host=os.getenv("CHROMA_HOST", "localhost"),
            port=int(os.getenv("CHROMA_PORT", 8000))
        )

        # Save chunks to ChromaDB
        client.ingest_chunks(chunks=content_chunks, collection_name="documents")
        logging.info(f"Successfully added {len(content_chunks)} document chunks to 'documents' collection")

        # Save images descriptions
        descriptions = [image.description for image in images]
        client.ingest_chunks(chunks=descriptions, collection_name="images")
        logging.info(f"Successfully added {len(descriptions)} descriptions to 'images' collection")

        return jsonify({"message": f"Successfully added documents ({len(content_chunks)}) and images description ({len(descriptions)})"}), 201
    except Exception as e:
        logging.error(f"Something went wrong: {e}")
        return jsonify({"error": "Something went wrong", "detail": str(e)}), 500