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
            pr_data = {
                "pr_number": payload["pull_request"]["number"],
                "title":     payload["pull_request"]["title"],
                "diff_url":  payload["pull_request"]["diff_url"],
                "body":      payload["pull_request"]["body"],
                "repo":      payload["repository"]["full_name"]
            }
            # Next: send pr_data to LLM agent
            print("PR received: {pr_data}")
            return {"status": "received", "pr": pr_data["pr_number"]}

    return {"status": "ignored"}