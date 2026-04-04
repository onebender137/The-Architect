import chromadb
from chromadb.utils import embedding_functions
import os
import asyncio
import logging
from rank_bm25 import BM25Okapi

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
        self.bm25 = None
        self.documents = []
        self.metadatas = []

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

    def _initialize_bm25(self):
        """Initializes BM25 with current documents in collection."""
        all_data = self.collection.get()
        self.documents = all_data['documents']
        self.metadatas = all_data['metadatas']
        if self.documents:
            tokenized_corpus = [doc.split() for doc in self.documents]
            self.bm25 = BM25Okapi(tokenized_corpus)

    async def search(self, query, n_results=3):
        """Hybrid Search: Combines Vector Search (Chroma) and Keyword Search (BM25)."""
        try:
            loop = asyncio.get_running_loop()

            # 1. Vector Search
            vector_results = await loop.run_in_executor(
                None,
                lambda: self.collection.query(
                    query_texts=[query],
                    n_results=n_results
                )
            )

            # 2. BM25 Fallback/Augmentation
            if not self.bm25:
                await loop.run_in_executor(None, self._initialize_bm25)

            if self.bm25:
                tokenized_query = query.split()
                bm25_docs = self.bm25.get_top_n(tokenized_query, self.documents, n=n_results)

                # Merge logic: Append BM25 results if they aren't already in vector results
                existing_docs = vector_results['documents'][0] if vector_results['documents'] else []
                for doc in bm25_docs:
                    if doc not in existing_docs:
                        # Find metadata for this doc
                        try:
                            idx = self.documents.index(doc)
                            vector_results['documents'][0].append(doc)
                            vector_results['metadatas'][0].append(self.metadatas[idx])
                        except ValueError:
                            continue

            return vector_results
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
            self.bm25 = None
            self.documents = []
            self.metadatas = []
            return True
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            return False
