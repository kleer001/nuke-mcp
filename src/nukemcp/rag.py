"""Documentation RAG — BM25 full-text search over Nuke docs. Pure stdlib, no dependencies."""

from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

INDEX_DIR = Path(__file__).parent.parent.parent / "rag_index"


@dataclass
class Document:
    id: str
    title: str
    content: str
    source: str  # "nuke_api", "nukepedia", "facility", "release_notes"
    tokens: list[str] = field(default_factory=list)


class BM25Index:
    """BM25 full-text search index. Pure Python, no external dependencies."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: list[Document] = []
        self.avgdl: float = 0.0
        self.doc_freqs: dict[str, int] = {}  # term -> number of docs containing it
        self.doc_term_freqs: list[Counter] = []  # per-doc term frequency

    def add_document(self, doc: Document):
        tokens = self._tokenize(doc.content + " " + doc.title)
        doc.tokens = tokens
        self.docs.append(doc)
        tf = Counter(tokens)
        self.doc_term_freqs.append(tf)
        for term in set(tokens):
            self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        # Update average doc length
        total = sum(len(d.tokens) for d in self.docs)
        self.avgdl = total / len(self.docs) if self.docs else 0.0

    def search(self, query: str, top_k: int = 5) -> list[tuple[Document, float]]:
        """Search the index and return top_k results with scores."""
        if not self.docs or self.avgdl == 0.0:
            return []
        query_tokens = self._tokenize(query)
        n = len(self.docs)
        scores = []

        for i, doc in enumerate(self.docs):
            score = 0.0
            dl = len(doc.tokens)
            tf_map = self.doc_term_freqs[i]

            for term in query_tokens:
                if term not in self.doc_freqs:
                    continue
                df = self.doc_freqs[term]
                idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)
                tf = tf_map.get(term, 0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += idf * numerator / denominator

            if score > 0:
                scores.append((doc, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def save(self, path: Path | None = None):
        """Save the index to disk as JSON."""
        path = path or INDEX_DIR / "index.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "docs": [
                {"id": d.id, "title": d.title, "content": d.content, "source": d.source}
                for d in self.docs
            ],
        }
        path.write_text(json.dumps(data), encoding="utf-8")
        log.info("Saved BM25 index with %d documents to %s", len(self.docs), path)

    def load(self, path: Path | None = None) -> bool:
        """Load the index from disk. Returns True if successful."""
        path = path or INDEX_DIR / "index.json"
        if not path.is_file():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        self.docs = []
        self.doc_freqs = {}
        self.doc_term_freqs = []
        for d in data["docs"]:
            doc = Document(id=d["id"], title=d["title"], content=d["content"], source=d["source"])
            self.add_document(doc)
        log.info("Loaded BM25 index with %d documents from %s", len(self.docs), path)
        return True

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + punctuation tokenizer."""
        text = text.lower()
        tokens = re.findall(r"[a-z0-9_]+", text)
        return tokens


def register(server):
    """Register RAG search tools."""
    mcp = server.mcp
    index = BM25Index()
    index.load()

    @mcp.tool(annotations={"readOnlyHint": True})
    def search_nuke_docs(query: str, top_k: int = 5) -> dict:
        """Search the Nuke documentation index for relevant information.

        Uses a BM25 full-text index over Nuke Python API docs, Nukepedia entries,
        and facility documentation.

        Args:
            query: Search query (e.g., "IBKGizmo knobs", "Deep compositing workflow").
            top_k: Number of results to return (default 5).
        """
        results = index.search(query, top_k)
        if not results:
            return {
                "query": query,
                "results": [],
                "message": "No results found. The RAG index may be empty — run scripts/ingest_docs.py to populate it.",
            }
        return {
            "query": query,
            "results": [
                {
                    "title": doc.title,
                    "source": doc.source,
                    "score": round(score, 3),
                    "content": doc.content[:500],
                }
                for doc, score in results
            ],
        }
