from app.ingestion.pipeline import chunk_pages


def test_chunk_pages_preserves_page_provenance_and_overlap():
    text = " ".join(f"clinical-record-word-{i}" for i in range(180))
    chunks = chunk_pages([(4, text)], size=300, overlap=60)
    assert len(chunks) > 1
    assert all(chunk["page"] == 4 for chunk in chunks)
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
    assert chunks[0]["text"][-30:] in chunks[1]["text"]


def test_chunk_pages_skips_empty_pages():
    assert chunk_pages([(1, "  "), (2, "Blood pressure recorded")]) == [
        {"page": 2, "text": "Blood pressure recorded", "chunk_index": 0}
    ]
