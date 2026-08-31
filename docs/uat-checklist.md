# Ghost QA — User Acceptance Testing Checklist

Run against the staging instance before promoting to production.
Login for scripted tests: seeded admin (`admin@ghost.qa` / `Admin123!`) — replace
with real test accounts during UAT.

## 1. Authentication & access control

- [ ] Login with valid credentials redirects to the dashboard
- [ ] Login with wrong password shows an error, no token issued
- [ ] Session persists across page reload (token stored)
- [ ] Logout clears the session and returns to /login
- [ ] Deep links while logged out bounce to /login and return after auth
- [ ] Viewer role cannot see Admin nav or approve tests
- [ ] Admin can reach /admin and manage users

## 2. Pipeline flow (webhook → tests → approval)

- [ ] GitHub PR webhook creates a pipeline run (use smoke payload or real repo)
- [ ] Run appears on Pipeline Runs page with correct repo/PR metadata
- [ ] AI-generated tests listed under the run with steps visible
- [ ] Approve All (approver role) moves run out of awaiting_approval
- [ ] Individual approve/reject works from the Test Case page
- [ ] Rejected test records the reason
- [ ] Risk report tab renders overall risk badge (not "unknown") and breakdown

## 3. Healing flow

- [ ] Proposed heal appears on its test with rationale
- [ ] Approve/Reject buttons only show for `proposed` heals
- [ ] Execute button only shows for `accepted` heals
- [ ] Heal attempt history displays original vs proposed steps

## 4. Dashboard & reporting

- [ ] Dashboard stat cards populate after at least one run
- [ ] Status/risk breakdowns match run list data
- [ ] Recent runs table links to run detail pages
- [ ] JSON risk report endpoint returns `risk_level` field

## 5. Non-functional

- [ ] Page load < 2s on staging hardware
- [ ] Layout usable at mobile width (sidebar drawer opens/closes)
- [ ] Error states show friendly messages (stop backend, refresh a page)
- [ ] No console errors during a full walkthrough
- [ ] Rate limiting returns 429 with Retry-After when hammered

## 6. Sign-off

| Role        | Name | Date | Result |
|-------------|------|------|--------|
| QA Engineer |      |      |        |
| Approver    |      |      |        |
| DevOps      |      |      |        |
