from app.core.supabase_client import supabase
from google.genai import types
from app.core.gemini_client import client
import requests


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

agent_tool = types.Tool(
    function_declarations=[search_matches_declaration, search_live_jobs_declaration]
)
AGENT_MODEL = "gemini-3.5-flash"


def run_agent(resume_id: str, user_goal: str) -> str:
    chat = client.chats.create(
        model=AGENT_MODEL, config=types.GenerateContentConfig(tools=[agent_tool])
    )
    response = chat.send_message(user_goal)

    if response.function_calls:
        call = response.function_calls[0]

        if call.name == "search_job_matches":
            tool_result = search_job_matches(resume_id, call.args.get("min_score", 70))
        elif call.name == "search_live_jobs":
            tool_result = search_live_jobs(
                call.args["query"], call.args.get("limit", 10)
            )
        else:
            tool_result = {"error": f"Unknown tool: {call.name}"}

        response = chat.send_message(
            types.Part.from_function_response(
                name=call.name, response={"result": tool_result}
            )
        )
        return response.text

    return response.text


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
