# 🧠 Neural Memory (RAG) Architecture

The Architect utilizes a **Retrieval-Augmented Generation (RAG)** system, referred to as **Neural Memory**, to provide persistent, local-first context from the codebase. This allows the agent to "remember" and reference files across the entire project without requiring them to be manually ingested into every conversation.

## 🛠️ Technical Stack

- **Vector Database:** [ChromaDB](https://www.trychroma.com/) (Persistent Local Storage)
- **Embedding Model:** `all-MiniLM-L6-v2` (via `sentence-transformers`)
- **Acceleration:** Runs on CPU or XPU (Intel Arc) via standard PyTorch/IPEX paths.

## 🚀 How it Works

1. **Indexing (`/reindex`):**
   - When the `/reindex` command is issued, The Architect crawls the project directory (excluding `.git`, `venv`, etc.).
   - It reads supported text files (`.py`, `.md`, `.sh`, `.txt`, `.bat`, `.json`) under 500KB.
   - Each file's content is converted into a vector embedding and stored in the local `chroma_db/` directory.

2. **Retrieval (Automatic):**
   - For every incoming message, The Architect performs a similarity search against the vector database.
   - The top 2 most relevant code blocks or documents are retrieved.
   - These blocks are injected into the LLM's system prompt as "RELEVANT PROJECT CONTEXT."

3. **Inference:**
   - The LLM (Dolphin-Mistral) uses both the conversation history and the retrieved context to generate highly accurate, project-specific responses.

## 📂 Configuration

- **Database Path:** `./chroma_db` (Ignored by Git)
- **Concurrency:** All RAG operations (indexing and searching) are executed in non-blocking threads using `asyncio.to_thread` to maintain bot responsiveness.

---
*Neural Memory transforms The Architect from a stateless assistant into a context-aware coding mentor.*
