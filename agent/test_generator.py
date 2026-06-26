# agent/test_generator.py
import anthropic
import requests

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

def fetch_pr_diff(diff_url: str, github_token: str) -> str:
    headers = {"Authorization": f"token {github_token}",
               "Accept": "application/vnd.github.v3.diff"}
    response = requests.get(diff_url, headers=headers)
    return response.text[:4000]  # limit tokens

def generate_test_cases(pr_title: str, pr_body: str, diff: str) -> dict:
    prompt = f"""
You are a senior QA engineer. Analyze this pull request and generate test cases.

PR Title: {pr_title}
PR Description: {pr_body}

Code Changes (diff):
{diff}

Generate exactly 5 test cases in this JSON format:
{{
  "test_cases": [
    {{
      "id": "TC001",
      "title": "short test title",
      "scenario": "what to test",
      "steps": ["step 1", "step 2"],
      "expected_result": "what should happen",
      "risk_level": "high|medium|low",
      "reason": "why this could break"
    }}
  ],
  "overall_risk": "high|medium|low",
  "summary": "one sentence risk summary"
}}

Return ONLY valid JSON. No explanation, no markdown.
"""
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    import json
    return json.loads(message.content[0].text)

# Test it locally:
if __name__ == "__main__":
    result = generate_test_cases(
        pr_title="Add user authentication endpoint",
        pr_body="Implements JWT login and signup",
        diff="+ def login(email, password): ..."
    )
    print(result)