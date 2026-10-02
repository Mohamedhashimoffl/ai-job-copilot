from dotenv import load_dotenv

load_dotenv()

from app.services.agent_tools import run_agent

result = run_agent(
    resume_id="004e52f9-4a16-4cf5-8d75-72263123e281",
    user_goal="What job matches do I have where the fit score is 70 or higher?",
)
print(result)

result2 = run_agent(
    resume_id="004e52f9-4a16-4cf5-8d75-72263123e281",
    user_goal="What's the capital of France?",
)
print(result2)
