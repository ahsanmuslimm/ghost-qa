from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import sys, os, json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent.test_generator import fetch_pr_diff, generate_test_cases

load_dotenv()
app = FastAPI()

@app.get("/")
def health():
    return {"status": "Ghost QA running"}

@app.post("/webhook")
async def github_webhook(request: Request):
    event = request.headers.get("X-GitHub-Event", "")
    payload = await request.json()

    if event != "pull_request":
        return {"status": "ignored", "event": event}

    action = payload.get("action", "")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "action": action}

    pr = payload["pull_request"]
    print(f"\n── PR #{pr['number']} received: {pr['title']} ──")

    diff = fetch_pr_diff(pr["diff_url"])
    test_cases = generate_test_cases(
        pr_title=pr["title"],
        pr_body=pr.get("body") or "No description provided",
        diff=diff
    )

    print(json.dumps(test_cases, indent=2))

    # Later: send to UiPath Test Cloud here
    # Later: post back to GitHub PR as comment here

    return {
        "status": "tests_generated",
        "pr_number": pr["number"],
        "test_count": len(test_cases["test_cases"]),
        "overall_risk": test_cases["overall_risk"],
        "summary": test_cases["summary"]
    }