from app.core.supabase_client import supabase
from google.genai import types
from app.core.gemini_client import client
import requests
from app.services.matcher import analyze_fit
import time
from app.services.embeddings import get_embedding


class AgentGuardrails:
    def __init__(
        self, max_turns: int = 6, max_tool_calls: int = 8, max_seconds: int = 60
    ):
        self.max_turns = max_turns
        self.max_tool_calls = max_tool_calls
        self.max_seconds = max_seconds
        self.start_time = time.time()
        self.tool_call_count = 0
        self.call_history: list[tuple[str, str]] = []

    def check_time(self):
        if time.time() - self.start_time > self.max_seconds:
            raise TimeoutError(f"Agent exceeded {self.max_seconds}s wall-clock limit")

    def check_tool_call(self, tool_name: str, args: dict):
        self.tool_call_count += 1
        if self.tool_call_count > self.max_tool_calls:
            raise RuntimeError(
                f"Agent exceeded {self.max_tool_calls} tool calls — stopping to protect quota"
            )
        signature = (tool_name, str(sorted(args.items())))
        if self.call_history.count(signature) >= 2:
            raise RuntimeError(
                f"Agent repeated the same call 3x ({tool_name}) — likely stuck, stopping"
            )
        self.call_history.append(signature)


def search_job_matches(resume_id: str, min_score: int = 70) -> list[dict]:
    """
    Tool: returns job matches for a resume above a minimum fit score.
    Queries the `matches` table populated by your Day 8 analysis.
    """
    result = (
        supabase.table("matches")
        .select("*, job_postings(title, company)")
        .eq("resume_id", resume_id)
        .gte("score", min_score)
        .execute()
    )
    return result.data


search_matches_declaration = types.FunctionDeclaration(
    name="search_job_matches",
    description="Get job matches for the user's resume with a fit score above a threshold.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "min_score": types.Schema(
                type="INTEGER",
                description="Minimum fit score (0-100) to include. Default 70.",
            )
        },
    ),
)

search_live_jobs_declaration = types.FunctionDeclaration(
    name="search_live_jobs",
    description="Search real, current remote job postings by keyword (e.g. job title or skill).",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "query": types.Schema(
                type="STRING",
                description="Search term, e.g. 'backend developer' or 'python'",
            ),
            "limit": types.Schema(
                type="INTEGER",
                description="Max number of results to return. Default 10.",
            ),
        },
        required=["query"],
    ),
)

score_job_declaration = types.FunctionDeclaration(
    name="score_job_against_resume",
    description="Score how well a specific job posting fits the resume (0-100).",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "job_title": types.Schema(type="STRING"),
            "job_url": types.Schema(type="STRING"),
        },
        required=["job_url"],
    ),
)

add_to_tracker_declaration = types.FunctionDeclaration(
    name="add_to_tracker",
    description="Add a job to the user's application tracker as a draft.",
    parameters=types.Schema(
        type="OBJECT",
        properties={"job_id": types.Schema(type="STRING")},
        required=["job_id"],
    ),
)

agent_tool = types.Tool(
    function_declarations=[
        search_matches_declaration,
        search_live_jobs_declaration,
        score_job_declaration,
        add_to_tracker_declaration,
    ]
)

AGENT_MODEL = "gemini-3.5-flash-lite"


def run_agent(user, resume_id: str, user_goal: str) -> str:
    guardrails = AgentGuardrails(max_turns=6, max_tool_calls=8, max_seconds=60)
    chat = client.chats.create(
        model=AGENT_MODEL, config=types.GenerateContentConfig(tools=[agent_tool])
    )
    response = chat.send_message(user_goal)
    live_jobs_cache = {}

    for _ in range(guardrails.max_turns):
        print(f"\n--- [TURN {_ + 1}] ---")

        # If no tool calls were requested, Gemini is providing its final text answer
        if not response.function_calls:
            final_text = (
                response.text
                or "Workflow completed. Relevant jobs were analyzed and processed."
            )
            return {"result": final_text, "tool_calls_used": guardrails.tool_call_count}

        call = response.function_calls[0]
        args = dict(call.args)
        print(f"[TOOL REQUESTED]: {call.name} with args: {args}")

        try:
            guardrails.check_tool_call(call.name, args)
        except (RuntimeError, TimeoutError) as e:
            return {
                "result": f"Stopped early: {e}",
                "tool_calls_used": guardrails.tool_call_count,
            }

        if call.name == "search_job_matches":
            tool_result = search_job_matches(resume_id, args.get("min_score", 70))
        elif call.name == "search_live_jobs":
            jobs = search_live_jobs(args["query"], args.get("limit", 10))
            for j in jobs:
                live_jobs_cache[j["url"]] = j
            tool_result = jobs
        elif call.name == "score_job_against_resume":
            job = live_jobs_cache.get(args.get("job_url"))
            if job:
                tool_result = score_job_against_resume(resume_id, job)
            else:
                tool_result = {
                    "error": "job not found in cache, search live jobs first"
                }
        elif call.name == "add_to_tracker":
            tool_result = add_to_tracker(user.id, args.get("job_id"))
        else:
            tool_result = {"error": f"Unknown tool: {call.name}"}

        print(f"[TOOL RESULT SUMMARY]: {str(tool_result)[:120]}...")

        # Send function result back to Gemini
        response = chat.send_message(
            types.Part.from_function_response(
                name=call.name, response={"result": tool_result}
            )
        )

    return {
        "result": "Stopped: max turns reached without a final answer.",
        "tool_calls_used": guardrails.tool_call_count,
    }


def search_live_jobs(query: str, limit: int = 10) -> list[dict]:
    """
    Tool: searches real, current remote job listings via the Remotive API.
    """
    response = requests.get(
        "https://remotive.com/api/remote-jobs", params={"search": query}, timeout=10
    )
    response.raise_for_status()
    jobs = response.json().get("jobs", [])[:limit]
    return [
        {
            "title": j["title"],
            "company": j["company_name"],
            "description": j["description"][:1000],
            "url": j["url"],
        }
        for j in jobs
    ]


def score_job_against_resume(resume_id: str, job: dict) -> dict:
    """
    Tool: scores a single job against the resume using the Day 7/8 pipeline.
    Inserts the live job into job_postings if it isn't there yet.
    """
    existing = (
        supabase.table("job_postings")
        .select("id")
        .eq("source_url", job["url"])
        .execute()
        .data
    )
    if existing:
        job_id = existing[0]["id"]
    else:
        inserted = (
            supabase.table("job_postings")
            .insert(
                {
                    "title": job["title"],
                    "company": job["company"],
                    "description": job["description"],
                    "source_url": job["url"],
                    "embedding": get_embedding(
                        job["description"], task_type="RETRIEVAL_DOCUMENT"
                    ),
                }
            )
            .execute()
        )
        job_id = inserted.data[0]["id"]

    job_row = (
        supabase.table("job_postings").select("*").eq("id", job_id).execute().data[0]
    )
    result = analyze_fit(resume_id, job_row)

    supabase.table("matches").upsert(
        {
            "resume_id": resume_id,
            "job_id": job_id,
            "score": result["score"],
            "explanation": result["explanation"],
            "strengths": result["strengths"],
            "gaps": result["gaps"],
        },
        on_conflict="resume_id,job_id",
    ).execute()

    return {"job_id": job_id, "title": job["title"], **result}


def add_to_tracker(user_id: str, job_id: str) -> dict:
    """Tool: creates a draft application for a job, reusing Day 10 logic."""
    existing = (
        supabase.table("applications")
        .select("id")
        .eq("user_id", user_id)
        .eq("job_id", job_id)
        .execute()
        .data
    )
    if existing:
        return {"status": "already_tracked", "application_id": existing[0]["id"]}
    result = (
        supabase.table("applications")
        .insert(
            {
                "user_id": user_id,
                "job_id": job_id,
                "status": "draft",
            }
        )
        .execute()
    )
    return {"status": "added", "application_id": result.data[0]["id"]}
