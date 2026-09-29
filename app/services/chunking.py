def chunk_resume(text: str, max_chars: int = 500, min_chars: int = 40) -> list[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chunks, current = [], ""
    for line in lines:
        if current and len(current) + len(line) + 1 > max_chars:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c) >= min_chars]
