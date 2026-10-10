from dotenv import load_dotenv

load_dotenv()

import os
from app.api import resumes
from fastapi import FastAPI
from app.api import auth, matches
from app.api import applications
from fastapi.responses import JSONResponse
from google.genai import errors as genai_errors

app = FastAPI()


@app.exception_handler(genai_errors.APIError)
async def gemini_error_handler(request, exc):
    return JSONResponse(
        status_code=503,
        content={
            "detail": "The AI service is busy or today's free quota is used up. Try again later."
        },
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
