from app.services.chunking import chunk_resume


def test_splits_long_text_into_multiple_chunks():
    text = "\n".join(f"Line {i} with some resume content here" for i in range(30))
    chunks = chunk_resume(text, max_chars=200, min_chars=20)
    assert len(chunks) > 1


def test_drops_tiny_fragments():
    text = "short"
    chunks = chunk_resume(text, min_chars=20)
    assert len(chunks) == 0


def test_single_short_resume_is_one_chunk():
    text = (
        "A reasonably sized paragraph of resume content that clears the minimum length."
    )
    chunks = chunk_resume(text, max_chars=500, min_chars=20)
    assert len(chunks) == 1
