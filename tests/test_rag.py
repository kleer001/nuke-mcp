"""Tests for BM25 RAG index."""

import shutil

import pytest

from nukemcp.rag import BM25Index, Document, INDEX_DIR


@pytest.fixture(autouse=True)
def clean_index():
    """Ensure clean RAG index directory."""
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    yield
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)


def test_add_and_search():
    idx = BM25Index()
    idx.add_document(Document(
        id="1", title="IBKGizmo Keying", content="IBKGizmo is used for green screen keying in Nuke", source="nuke_api",
    ))
    idx.add_document(Document(
        id="2", title="Grade Node", content="Grade node adjusts color using lift gamma gain", source="nuke_api",
    ))

    results = idx.search("green screen keying")
    assert len(results) > 0
    assert results[0][0].id == "1"


def test_search_empty_index():
    idx = BM25Index()
    results = idx.search("anything")
    assert results == []


def test_save_and_load():
    idx = BM25Index()
    idx.add_document(Document(
        id="doc1", title="Test", content="Test document content for save load", source="test",
    ))
    idx.save()

    idx2 = BM25Index()
    loaded = idx2.load()
    assert loaded is True
    assert len(idx2.docs) == 1
    assert idx2.docs[0].id == "doc1"


def test_load_nonexistent():
    idx = BM25Index()
    assert idx.load() is False


def test_tokenizer():
    tokens = BM25Index._tokenize("Hello World! This is a test_123.")
    assert "hello" in tokens
    assert "world" in tokens
    assert "test_123" in tokens


def test_multiple_results_ranked():
    idx = BM25Index()
    idx.add_document(Document(
        id="1", title="Nuke", content="nuke compositing", source="test",
    ))
    idx.add_document(Document(
        id="2", title="Nuke Keying", content="nuke keying with IBKGizmo chromakey green", source="test",
    ))
    idx.add_document(Document(
        id="3", title="Other", content="something unrelated entirely", source="test",
    ))

    results = idx.search("nuke keying green")
    assert len(results) >= 2
    # The keying doc should rank higher
    assert results[0][0].id == "2"
