import chromadb
from chromadb.utils import embedding_functions
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name="neural_memory",
            embedding_function=self.embedding_function
        )

    async def add_document(self, text, metadata=None, doc_id=None):
        """Adds a document to the vector store asynchronously."""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: self.collection.add(
                    documents=[text],
                    metadatas=[metadata] if metadata else None,
                    ids=[doc_id] if doc_id else [os.urandom(8).hex()]
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add document to memory: {e}")
            return False

    async def search(self, query, n_results=3):
        """Queries the vector store for relevant documents asynchronously."""
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            )
            return results
        except Exception as e:
            logger.error(f"Search in memory failed: {e}")
            return None

    async def clear_memory(self):
        """Clears all entries in the collection."""
        try:
            self.client.delete_collection("neural_memory")
            self.collection = self.client.get_or_create_collection(
                name="neural_memory",
                embedding_function=self.embedding_function
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
