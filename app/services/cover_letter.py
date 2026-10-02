from app.core.gemini_client import client
import time

WRITER_MODEL = "gemini-3.5-flash"


def generate_cover_letter(resume_context: str, job: dict, match: dict) -> str:
    strengths_text = "\n".join(f"- {s}" for s in match.get("strengths") or [])

    prompt = f"""You are helping a candidate write a short, honest cover letter.

JOB:
Title: {job["title"]}
Company: {job.get("company", "the company")}
Description: {job["description"]}

CANDIDATE'S RELEVANT RESUME EVIDENCE:
{resume_context}

CONFIRMED STRENGTHS FOR THIS ROLE:
{strengths_text}

Write a cover letter (150-200 words) that:
- Opens with genuine, specific interest in this role (not generic enthusiasm)
- References 2-3 concrete pieces of resume evidence from above, not vague claims
- Sounds like a real early-career candidate, not corporate marketing copy
- Does NOT mention gaps, weaknesses, or anything not in the strengths list
- Ends with a short, direct closing line — no "I look forward to hearing from you" cliché

Write only the letter body. No subject line, no placeholders like [Company Name]."""

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=WRITER_MODEL, contents=prompt
            )
            return response.text
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2)
