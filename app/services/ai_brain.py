import json
import hashlib
import logging
import re
import time
from typing import List, Dict, Any, Optional
try:
    from openai import OpenAI
    _has_openai = True
except ImportError:
    _has_openai = False
try:
    from google import genai
    from google.genai import types as genai_types
    _has_genai = True
except ImportError:
    _has_genai = False
from app.config import settings
from app.schemas.test_schemas import TestCaseSchema, TestStepSchema, AITestResponse, TestDebtFinding, TestDebtReport
from app.models import TestType, TestPriority, RiskLevel

logger = logging.getLogger(__name__)


class AIBrainService:
    CACHE_MAX_ENTRIES = 100
    CACHE_TTL_SECONDS = 3600

    def __init__(self):
        self.gemini_client = None
        self.xai_client = None
        self.anthropic_client = None
        self._cache: Dict[str, Dict[str, Any]] = {}

        # Gemini (primary provider — free tier)
        gemini_key = settings.GEMINI_API_KEY
        if gemini_key:
            if _has_genai:
                self.gemini_client = genai.Client(api_key=gemini_key)
            else:
                logger.warning("google-genai package not installed; Gemini unavailable")

        # XAI (Grok) fallback — key must start with 'xai-' (or 'sk-' for proxies)
        xai_key = settings.XAI_API_KEY
        if xai_key and _has_openai and xai_key.startswith(("xai-", "sk-")):
            self.xai_client = OpenAI(
                api_key=xai_key,
                base_url="https://api.x.ai/v1"
            )
        elif xai_key:
            logger.warning(f"XAI API key format unrecognized, falling back to demo mode")

        # Anthropic Claude fallback — key must start with 'sk-ant-'
        anthropic_key = settings.ANTHROPIC_API_KEY
        if anthropic_key and anthropic_key.startswith("sk-ant-"):
            try:
                from anthropic import Anthropic
                self.anthropic_client = Anthropic(api_key=anthropic_key)
            except ImportError:
                logger.warning("anthropic package not installed; Anthropic unavailable")
        elif anthropic_key:
            logger.warning(f"Anthropic API key format unrecognized, falling back to demo mode")

        # Resolve active provider: explicit AI_PROVIDER wins, otherwise auto
        # precedence Gemini → Anthropic → XAI → demo.
        self.provider = self._resolve_provider()
        self.demo_mode = settings.DEMO_MODE or self.provider == "demo"
        if not self.demo_mode:
            logger.info(f"AI Brain active with provider: {self.provider}")

    def _resolve_provider(self) -> str:
        requested = (settings.AI_PROVIDER or "auto").lower()
        available = {
            "gemini": self.gemini_client is not None,
            "anthropic": self.anthropic_client is not None,
            "xai": self.xai_client is not None,
        }
        if requested == "demo":
            return "demo"
        if requested in available:
            if available[requested]:
                return requested
            logger.warning(f"AI_PROVIDER={requested} requested but not configured, using auto selection")
        for name in ("gemini", "anthropic", "xai"):
            if available[name]:
                return name
        return "demo"

    def _call_ai(self, prompt: str, system_prompt: str = "", max_tokens: int = 4096) -> str:
        if self.demo_mode:
            return self._generate_demo_response(prompt, system_prompt)
        try:
            if self.provider == "gemini":
                response = self.gemini_client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_prompt or None,
                        max_output_tokens=max_tokens,
                    )
                )
                return response.text
            elif self.provider == "xai":
                model = settings.GROK_MODEL
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})
                response = self.xai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=5
                )
                return response.choices[0].message.content
            elif self.provider == "anthropic":
                message = self.anthropic_client.messages.create(
                    model=settings.ANTHROPIC_MODEL,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text
            else:
                raise RuntimeError("No AI provider configured")
        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return self._generate_demo_response(prompt, system_prompt)

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw.strip())
        except json.JSONDecodeError:
            # Attempt to find JSON in the response
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"Failed to parse JSON from AI response: {raw[:500]}")

    def generate_tests(
        self,
        pr_title: str,
        pr_body: str,
        diff: str,
        changed_files: List[str],
        linked_issue: Optional[Dict[str, Any]] = None,
        existing_tests: List[str] = None
    ) -> AITestResponse:
        cache_key = self._cache_key("generate_tests", pr_title, pr_body, diff, changed_files)
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.info("generate_tests cache hit — reusing cached test suite")
            return cached

        system_prompt = """You are a senior QA engineer specializing in AI-powered test generation.
Analyze pull request changes and generate contextual, meaningful test cases.
Focus on the PURPOSE of the change, not generic tests.
Return ONLY valid JSON, no markdown, no explanations outside the JSON."""

        issue_context = ""
        if linked_issue:
            issue_context = f"\nLinked Issue:\n- Title: {linked_issue.get('title', '')}\n- Body: {linked_issue.get('body', '')}\n"

        existing_context = ""
        if existing_tests:
            existing_context = f"\nExisting Test Files:\n" + "\n".join(f"- {t}" for t in existing_tests[:10])

        prompt = f"""Analyze this pull request and generate exactly 5 relevant test cases.

PR Title: {pr_title}
PR Description: {pr_body}
{issue_context}
Changed Files:
{chr(10).join(changed_files) if changed_files else "No specific files provided"}

Code Diff:
{diff[:4000]}
{existing_context}

Return ONLY this JSON structure, nothing else:
{{
  "tests": [
    {{
      "id": "TC-001",
      "title": "short descriptive test title",
      "type": "functional|regression|edge_case|integration",
      "priority": "p0_critical|p1_high|p2_medium|p3_low",
      "steps": [
        {{
          "action": "description of action",
          "selector": "CSS/XPath selector if applicable",
          "value": "input value if applicable",
          "assertion": "what to verify"
        }}
      ],
      "expected_result": "what should happen when test passes",
      "risk_level": "high|medium|low",
      "risk_rationale": "why this test is important given the change"
    }}
  ]
}}"""

        raw = self._call_ai(prompt, system_prompt=system_prompt)
        try:
            tests = self._transform_tests(self._parse_json(raw))
        except Exception as e:
            logger.error(f"Failed to parse AI response, falling back to demo tests: {e}")
            tests = []
        if not tests:
            # Parse failed or AI returned no usable tests — use demo fallback
            demo_raw = self._generate_demo_response(prompt, system_prompt)
            tests = self._transform_tests(self._parse_json(demo_raw))
        response = AITestResponse(tests=tests)
        self._cache_put(cache_key, response)
        return response

    def _transform_tests(self, data: Dict[str, Any]) -> List[TestCaseSchema]:
        tests = []
        for t in data.get("tests", []):
            try:
                tests.append(TestCaseSchema(
                    id=t.get("id", f"TC-{len(tests)+1:03d}"),
                    title=t.get("title", "Untitled test"),
                    type=TestType(t.get("type", "functional")),
                    priority=TestPriority(t.get("priority", "p2_medium")),
                    steps=[TestStepSchema(**s) for s in t.get("steps", [])],
                    expected_result=t.get("expected_result"),
                    risk_level=RiskLevel(t.get("risk_level", "medium")),
                    risk_rationale=t.get("risk_rationale")
                ))
            except Exception as e:
                logger.warning(f"Failed to parse test case: {e}")
                continue
        return tests

    def _cache_key(self, *parts: Any) -> str:
        return hashlib.md5(json.dumps(parts, default=str).encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> Optional[AITestResponse]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if time.time() - entry["timestamp"] < self.CACHE_TTL_SECONDS:
            return entry["response"]
        self._cache.pop(key, None)
        return None

    def _cache_put(self, key: str, response: AITestResponse) -> None:
        if len(self._cache) >= self.CACHE_MAX_ENTRIES:
            oldest = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
            self._cache.pop(oldest, None)
        self._cache[key] = {"response": response, "timestamp": time.time()}

    def detect_test_debt(
        self,
        changed_files: List[str],
        diff: str,
        existing_tests: List[str]
    ) -> TestDebtReport:
        system_prompt = """You are a QA architect analyzing test coverage gaps.
Identify missing, outdated, or stale tests based on code changes.
Return ONLY valid JSON, no markdown."""

        prompt = f"""Analyze these changed files for test debt.

Changed Files:
{chr(10).join(changed_files) if changed_files else "None provided"}

Code Diff:
{diff[:4000]}

Existing Test Files:
{chr(10).join(existing_tests) if existing_tests else "None found"}

Return ONLY this JSON structure:
{{
  "findings": [
    {{
      "affected_file": "path/to/file.py",
      "finding": "description of the debt",
      "reason": "why this is a problem",
      "risk": "high|medium|low",
      "recommendation": "what should be done"
    }}
  ]
}}"""

        raw = self._call_ai(prompt, system_prompt=system_prompt, max_tokens=2048)
        data = self._parse_json(raw)
        findings = []
        for f in data.get("findings", []):
            try:
                findings.append(TestDebtFinding(
                    affected_file=f.get("affected_file", ""),
                    finding=f.get("finding", ""),
                    reason=f.get("reason", ""),
                    risk=RiskLevel(f.get("risk", "medium")),
                    recommendation=f.get("recommendation", "")
                ))
            except Exception as e:
                logger.warning(f"Failed to parse test debt finding: {e}")
                continue
        return TestDebtReport(findings=findings)

    def propose_heal(
        self,
        test_title: str,
        original_steps: str,
        failure_type: str,
        failure_message: str,
        current_ui: Optional[str] = None,
        current_api_spec: Optional[str] = None
    ) -> Dict[str, Any]:
        system_prompt = """You are a QA automation expert specializing in test self-healing.
Analyze test failures and propose corrected test steps.
Return ONLY valid JSON, no markdown."""

        context = ""
        if current_ui:
            context += f"\nCurrent UI:\n{current_ui}\n"
        if current_api_spec:
            context += f"\nCurrent API Spec:\n{current_api_spec}\n"

        prompt = f"""A test failed. Propose a fix.

Test Title: {test_title}
Original Steps:
{original_steps}

Failure Type: {failure_type}
Failure Message: {failure_message}
{context}

Return ONLY this JSON structure:
{{
  "proposed_steps": "corrected step-by-step instructions",
  "rationale": "why this fix should work",
  "confidence": "high|medium|low"
}}"""

        raw = self._call_ai(prompt, system_prompt=system_prompt, max_tokens=2048)
        data = self._parse_json(raw)
        return {
            "proposed_steps": data.get("proposed_steps", original_steps),
            "rationale": data.get("rationale", "No rationale provided"),
            "confidence": data.get("confidence", "medium")
        }

    def _generate_demo_response(self, prompt: str, system_prompt: str = "") -> str:
        combined = (system_prompt + " " + prompt).lower()
        if "test debt" in combined or "test coverage gaps" in combined:
            return json.dumps({
                "findings": [
                    {
                        "affected_file": "src/auth/login.py",
                        "finding": "No test for invalid password scenario",
                        "reason": "Login endpoint was added but negative test cases are missing",
                        "risk": "high",
                        "recommendation": "Add test for invalid password, non-existent user, and rate limiting"
                    }
                ]
            })
        if "self-healing" in combined or "propose a correct" in combined:
            return json.dumps({
                "proposed_steps": "1. Navigate to login page\n2. Enter valid email\n3. Enter valid password\n4. Click #proceed-payment button\n5. Verify redirect to dashboard",
                "rationale": "The UI element was renamed from #checkout to #proceed-payment but the underlying functionality remains the same.",
                "confidence": "high"
            })
        # Default test generation
        return json.dumps({
            "tests": [
                {
                    "id": "TC-001",
                    "title": "Valid login with correct credentials",
                    "type": "functional",
                    "priority": "p0_critical",
                    "steps": [
                        {"action": "Navigate to login page", "selector": "#login-page", "value": "", "assertion": "Page loads successfully"},
                        {"action": "Enter email", "selector": "#email", "value": "user@example.com", "assertion": ""},
                        {"action": "Enter password", "selector": "#password", "value": "SecurePass123", "assertion": ""},
                        {"action": "Click submit", "selector": "#submit-login", "value": "", "assertion": ""},
                        {"action": "Verify JWT token received", "selector": "", "value": "", "assertion": "Response contains valid JWT"}
                    ],
                    "expected_result": "User receives JWT token and is authenticated",
                    "risk_level": "high",
                    "risk_rationale": "Authentication is a critical security path"
                },
                {
                    "id": "TC-002",
                    "title": "Invalid login with wrong password",
                    "type": "functional",
                    "priority": "p1_high",
                    "steps": [
                        {"action": "Navigate to login page", "selector": "#login-page", "value": "", "assertion": ""},
                        {"action": "Enter valid email", "selector": "#email", "value": "user@example.com", "assertion": ""},
                        {"action": "Enter wrong password", "selector": "#password", "value": "WrongPass", "assertion": ""},
                        {"action": "Click submit", "selector": "#submit-login", "value": "", "assertion": "Error message displayed"}
                    ],
                    "expected_result": "Login fails with appropriate error message",
                    "risk_level": "high",
                    "risk_rationale": "Invalid credentials must be rejected securely"
                },
                {
                    "id": "TC-003",
                    "title": "Login with non-existent user",
                    "type": "edge_case",
                    "priority": "p1_high",
                    "steps": [
                        {"action": "Navigate to login page", "selector": "#login-page", "value": "", "assertion": ""},
                        {"action": "Enter non-existent email", "selector": "#email", "value": "nobody@example.com", "assertion": ""},
                        {"action": "Enter any password", "selector": "#password", "value": "any", "assertion": ""},
                        {"action": "Click submit", "selector": "#submit-login", "value": "", "assertion": "Generic error message (no user enumeration)"}
                    ],
                    "expected_result": "Login fails with generic error, no user enumeration",
                    "risk_level": "medium",
                    "risk_rationale": "Security best practice: avoid revealing whether an email exists"
                },
                {
                    "id": "TC-004",
                    "title": "JWT token expiration handling",
                    "type": "integration",
                    "priority": "p2_medium",
                    "steps": [
                        {"action": "Login and obtain JWT", "selector": "", "value": "", "assertion": "Token received"},
                        {"action": "Wait for token expiration", "selector": "", "value": "", "assertion": ""},
                        {"action": "Call protected endpoint with expired token", "selector": "", "value": "", "assertion": "401 Unauthorized returned"}
                    ],
                    "expected_result": "Expired tokens are rejected with 401",
                    "risk_level": "medium",
                    "risk_rationale": "Expired tokens should not grant access"
                },
                {
                    "id": "TC-005",
                    "title": "SQL injection resistance in login",
                    "type": "edge_case",
                    "priority": "p0_critical",
                    "steps": [
                        {"action": "Navigate to login page", "selector": "#login-page", "value": "", "assertion": ""},
                        {"action": "Enter SQL injection payload", "selector": "#email", "value": "admin' OR '1'='1", "assertion": ""},
                        {"action": "Enter random password", "selector": "#password", "value": "x", "assertion": ""},
                        {"action": "Click submit", "selector": "#submit-login", "value": "", "assertion": "Login fails, no SQL error exposed"}
                    ],
                    "expected_result": "SQL injection attempt is blocked, login fails safely",
                    "risk_level": "critical",
                    "risk_rationale": "SQL injection in authentication is a critical vulnerability"
                }
            ]
        })
