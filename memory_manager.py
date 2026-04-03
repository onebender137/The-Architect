import os
import chromadb
from chromadb.utils import embedding_functions
import logging
from typing import List
import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MemoryManager")

class MemoryManager:
    def __init__(self, collection_name="architect_project", persist_directory="./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        # Using a reliable default: all-MiniLM-L6-v2 (runs well on CPU)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def _index_project_sync(self, root_dir="."):
        """Synchronous part of project indexing."""
        ignore_dirs = [".git", "__pycache__", "venv", ".venv", "chroma_db", "node_modules", "library"]
        ignore_files = ["architect.log", "check_ollama.py", "verify_rag.py", "check_models.py"]

        documents = []
        metadatas = []
        ids = []

        logger.info(f"Starting indexing of {root_dir}...")

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if file in ignore_files:
                    continue

                # Only index relevant text-based files
                if file.endswith(('.py', '.md', '.txt', '.sh', '.bat', '.template', '.json', '.env')):
                    filepath = os.path.relpath(os.path.join(root, file), root_dir)
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            content = f.read()

                        if not content.strip():
                            continue

                        # Chunking
                        chunks = self._chunk_text(content)
                        for i, chunk in enumerate(chunks):
                            documents.append(chunk)
                            metadatas.append({"source": filepath, "chunk": i})
                            ids.append(f"{filepath}_{i}")
                    except Exception as e:
                        logger.error(f"Failed to index {filepath}: {e}")

        if documents:
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                self.collection.upsert(
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )
            logger.info(f"✅ Indexed {len(documents)} chunks from project.")
            return len(documents)
        return 0

    async def index_project(self, root_dir="."):
        """Asynchronous wrapper for project indexing."""
        return await asyncio.to_thread(self._index_project_sync, root_dir)

    def _chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
        """Simple sliding window chunking."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += (chunk_size - overlap)
        return chunks

    def _search_sync(self, query: str, n_results: int = 3) -> str:
        """Synchronous similarity search."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        if not results['documents'] or not results['documents'][0]:
            return ""

        context_parts = []
        for i, doc in enumerate(results['documents'][0]):
            source = results['metadatas'][0][i]['source']
            context_parts.append(f"--- [SOURCE: {source}] ---\n{doc}")

        return "\n\n".join(context_parts)

    async def search(self, query: str, n_results: int = 3) -> str:
        """Asynchronous similarity search wrapper."""
        return await asyncio.to_thread(self._search_sync, query, n_results)

# Singleton for easy access
memory_manager = MemoryManager()
