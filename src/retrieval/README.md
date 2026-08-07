# Retrieval

Provides backend-agnostic lexical, dense, sequential and hybrid retrieval.

Input: query sequence/text, knowledge-base records and metadata filters.

Output: ranked `RetrievalItem` records with scores, ranks and evidence IDs.

Dependencies: BM25, FAISS and embedding libraries are deferred until Phase 3.

Planned files: `interfaces.py`, `bm25.py`, `dense.py`, `embeddings.py`, `sequential_similarity.py`, `hybrid.py`.

Implementation status: no index has been built and no retrieval code has started.
