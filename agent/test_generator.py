import google.generativeai as genai
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def fetch_pr_diff(diff_url: str) -> str:
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3.diff"
    }
    response = requests.get(diff_url, headers=headers)
    return response.text[:4000]

def generate_test_cases(pr_title: str, pr_body: str, diff: str) -> dict:
    prompt = f"""
You are a senior QA engineer reviewing a pull request.
Analyze the changes and generate exactly 5 test cases.

PR Title: {pr_title}
PR Description: {pr_body}

Code Diff:
{diff}

Return ONLY this JSON structure, nothing else, no markdown:
{{
  "test_cases": [
    {{
      "id": "TC001",
      "title": "short test title",
      "scenario": "what exactly to test",
      "steps": ["step 1", "step 2", "step 3"],
      "expected_result": "what should happen",
      "risk_level": "high|medium|low",
      "reason": "why this specific change could break something"
    }}
  ],
  "overall_risk": "high|medium|low",
  "summary": "one sentence describing the biggest risk in this PR"
}}
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown if Gemini wraps it anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    
    return json.loads(raw.strip())


# ── Local test — run this file directly to verify it works ──
if __name__ == "__main__":
    fake_diff = """
+ def login(email: str, password: str):
+     user = db.query(User).filter(User.email == email).first()
+     if user and verify_password(password, user.hashed_password):
+         return create_jwt_token(user.id)
+     return None
"""
    result = generate_test_cases(
        pr_title="Add login endpoint",
        pr_body="Implements JWT-based login for users",
        diff=fake_diff
    )
    print(json.dumps(result, indent=2))