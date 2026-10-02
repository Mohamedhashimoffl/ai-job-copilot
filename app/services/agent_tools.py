from app.core.supabase_client import supabase
from google.genai import types
from app.core.gemini_client import client


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

agent_tool = types.Tool(function_declarations=[search_matches_declaration])
AGENT_MODEL = "gemini-3.5-flash"


def run_agent(resume_id: str, user_goal: str) -> str:
    chat = client.chats.create(
        model=AGENT_MODEL, config=types.GenerateContentConfig(tools=[agent_tool])
    )
    response = chat.send_message(user_goal)

    if response.function_calls:
        call = response.function_calls[0]
        if call.name == "search_job_matches":
            min_score = call.args.get("min_score", 70)
            tool_result = search_job_matches(resume_id, min_score)

            response = chat.send_message(
                types.Part.from_function_response(
                    name="search_job_matches", response={"matches": tool_result}
                )
            )
            return response.text

    return response.text
