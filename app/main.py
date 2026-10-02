from dotenv import load_dotenv

load_dotenv()

import os
from app.api import resumes
from fastapi import FastAPI
from app.api import auth, matches
from app.api import applications

app = FastAPI()
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
app.include_router(matches.router, prefix="/matches", tags=["matches"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
