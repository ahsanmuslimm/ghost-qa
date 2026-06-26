# webhook/main.py
from fastapi import FastAPI, Request
from agent.test_generator import fetch_pr_diff, generate_test_cases
import hmac, hashlib, json

app = FastAPI()

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")

    if event == "pull_request":
        action = payload.get("action")
        if action in ["opened", "synchronize"]:
            diff = fetch_pr_diff(
                payload["pull_request"]["diff_url"],
                GITHUB_TOKEN
            )
            test_cases = generate_test_cases(
                pr_title=payload["pull_request"]["title"],
                pr_body=payload["pull_request"]["body"] or "",
                diff=diff
            )
            print(json.dumps(test_cases, indent=2))
            return {"status": "tests_generated", "cases": len(test_cases["test_cases"])}

    return {"status": "ignored"}