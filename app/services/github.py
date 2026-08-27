import hashlib
import hmac
import json
import logging
from typing import Optional, Dict, Any, List
import requests
from app.config import settings
from app.utils.retry import with_retry

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30


class GitHubService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.webhook_secret = settings.GITHUB_WEBHOOK_SECRET
        self.base_url = settings.GITHUB_API_BASE.rstrip("/")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.demo_mode = settings.DEMO_MODE and (not self.token or self.token == "None")

    def verify_signature(self, payload_bytes: bytes, signature_header: str) -> bool:
        if not self.webhook_secret or not signature_header:
            return True  # Skip verification if no secret configured
        try:
            algorithm, signature = signature_header.split("=", 1)
            if algorithm != "sha256":
                return False
            expected = hmac.new(
                self.webhook_secret.encode("utf-8"),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    @with_retry(attempts=3, backoff=1.0, retry_on=(requests.exceptions.ConnectionError, requests.exceptions.Timeout))
    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        if self.demo_mode:
            return {}
        response = requests.request(method, url, headers=self.headers, timeout=REQUEST_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else {}

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        if self.demo_mode:
            return {
                "id": 123456,
                "name": repo,
                "full_name": f"{owner}/{repo}",
                "default_branch": "main",
                "private": False
            }
        return self._request("GET", f"{self.base_url}/repos/{owner}/{repo}")

    def get_pr(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        if self.demo_mode:
            return {
                "number": pr_number,
                "title": "Demo PR",
                "body": "Demo pull request",
                "state": "open",
                "diff_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff",
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
                "head": {"ref": "feature-branch", "sha": "abc123"},
                "base": {"ref": "main", "sha": "def456"},
                "user": {"login": "demo-user"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        return self._request("GET", f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}")

    def get_changed_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        if self.demo_mode:
            return [
                {"filename": "src/auth/login.py", "status": "modified", "additions": 15, "deletions": 3},
                {"filename": "tests/test_auth.py", "status": "modified", "additions": 8, "deletions": 2}
            ]
        data = self._request("GET", f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files")
        return data

    def get_pr_diff(self, diff_url: str) -> str:
        if self.demo_mode:
            return """diff --git a/src/auth/login.py b/src/auth/login.py
+ def login(email: str, password: str):
+     user = db.query(User).filter(User.email == email).first()
+     if user and verify_password(password, user.hashed_password):
+         return create_jwt_token(user.id)
+     return None
"""
        response = requests.get(diff_url, headers={
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff"
        }, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text[:8000]

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> str:
        if self.demo_mode:
            return "# Demo file content\n"
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
        data = self._request("GET", url)
        import base64
        return base64.b64decode(data.get("content", "")).decode("utf-8")

    def get_existing_tests(self, owner: str, repo: str, ref: str = "main") -> List[str]:
        if self.demo_mode:
            return ["tests/test_auth.py", "tests/test_payment.py"]
        # In production, search for test files
        return []

    def get_linked_issue(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        if self.demo_mode:
            return {
                "number": 42,
                "title": "Implement login endpoint",
                "body": "Add JWT-based login for users"
            }
        pr = self.get_pr(owner, repo, pr_number)
        body = pr.get("body", "") or ""
        import re
        matches = re.findall(rf"{owner}/{repo}#(\d+)", body)
        if not matches:
            matches = re.findall(r"#(\d+)", body)
        if matches:
            try:
                return self._request("GET", f"{self.base_url}/repos/{owner}/{repo}/issues/{matches[0]}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Linked issue #{matches[0]} not found, skipping")
                    return None
                raise
        return None

    def post_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> Dict[str, Any]:
        if self.demo_mode:
            logger.info(f"[DEMO] Would post comment to {owner}/{repo}#{pr_number}")
            return {"id": 999, "body": body}
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        return self._request("POST", url, json={"body": body})

    def update_commit_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        description: str,
        context: str = "Ghost QA"
    ) -> Dict[str, Any]:
        if self.demo_mode:
            logger.info(f"[DEMO] Would update commit status {sha} to {state}")
            return {"state": state}
        url = f"{self.base_url}/repos/{owner}/{repo}/statuses/{sha}"
        return self._request("POST", url, json={
            "state": state,
            "description": description,
            "context": context
        })

    def extract_pr_info(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        return {
            "repo_full_name": repo.get("full_name", ""),
            "repo_owner": repo.get("owner", {}).get("login", ""),
            "repo_name": repo.get("name", ""),
            "pr_number": pr.get("number"),
            "pr_title": pr.get("title", ""),
            "pr_body": pr.get("body", "") or "",
            "pr_state": pr.get("state", ""),
            "branch": pr.get("head", {}).get("ref", ""),
            "commit_sha": pr.get("head", {}).get("sha", ""),
            "diff_url": pr.get("diff_url", ""),
            "html_url": pr.get("html_url", ""),
            "user": pr.get("user", {}).get("login", ""),
            "created_at": pr.get("created_at", ""),
            "updated_at": pr.get("updated_at", "")
        }
