import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.security import get_current_user, get_token
from app.core.supabase_client import supabase
from app.services.embeddings import get_embedding, get_embeddings
from app.services.resume_parser import extract_text_from_pdf
from app.services.chunking import chunk_resume

router = APIRouter()


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    token: str = Depends(get_token),
):
    supabase.postgrest.auth(token)

    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=400, detail="Only PDF or plain text supported")

    contents = await file.read()

    if file.content_type == "application/pdf":
        raw_text = extract_text_from_pdf(io.BytesIO(contents))
    else:
        raw_text = contents.decode("utf-8")

    if not raw_text.strip():
        raise HTTPException(
            status_code=422, detail="Couldn't extract any text from this file"
        )

    embedding = get_embedding(raw_text, task_type="retrieval_document")
    print(f"Generated embedding of length {len(embedding)} for resume")

    result = (
        supabase.table("resumes")
        .insert(
            {
                "user_id": user.id,
                "raw_text": raw_text,
                "file_name": file.filename,
                "embedding": embedding,
            }
        )
        .execute()
    )

    resume_id = result.data[0]["id"]

    chunks = chunk_resume(raw_text)
    if chunks:
        vectors = get_embeddings(chunks, task_type="RETRIEVAL_DOCUMENT")
        supabase.table("resume_chunks").insert(
            [
                {"resume_id": resume_id, "chunk_text": text, "embedding": vec}
                for text, vec in zip(chunks, vectors)
            ]
        ).execute()

    return {
        "resume_id": resume_id,
        "char_count": len(raw_text),
        "chunk_count": len(chunks),
    }
