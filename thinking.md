# Thinking Questions

## 1. A guest complains at 3am about hot water not working. What should the AI reply right now?

> "Hi Rahul, I'm very sorry about the hot water issue. I've immediately alerted our on-call support team and marked this as urgent. Someone will contact you shortly to resolve this before your breakfast guests arrive."

This reply acknowledges the problem, confirms action is being taken, and sets a clear expectation — but it should NOT be auto-sent. The system should generate this as a draft and escalate it immediately. Complaints always route to escalate regardless of confidence score. At 3am, the escalation triggers a push notification to the on-call property manager who can verify the caretaker has been contacted before the message goes out. For non-complaint queries (availability, pricing), auto-send works well — guests expect instant answers for these. The right model is: draft always, send selectively. Auto-send covers roughly 60-70% of volume (repetitive informational queries), freeing agents to focus on the 30% that needs human judgment.

## 2. System Escalation Workflow — How should escalation work when AI confidence is low?

Three-tier routing: auto_send (confidence > 0.85), agent_review (0.60–0.85), and escalate (< 0.60 or complaint). When a message is escalated, it enters a priority queue visible to on-duty staff with the AI draft attached as a suggestion — not as a starting point they must edit, but as reference. Escalated messages should trigger a push notification to the assigned property manager. SLA targets: agent_review messages handled within 15 minutes, escalated within 5 minutes. If an escalated message is not picked up within the SLA, it auto-routes to a senior manager. The AI draft is always visible so agents are not starting from scratch, but the system must make it clear the draft was NOT sent to the guest.

## 3. Learning From Repeated Complaints — How should the system improve over time?

Track complaint frequency by category (cleanliness, amenities, noise, staff behavior) and property. When the same complaint type crosses a threshold (e.g., 3 occurrences in 30 days for one property), trigger an automated operational alert to the property manager — this is not an AI problem, it is an operations problem. On the AI side, store agent edits alongside AI drafts in ai_processing. Periodically review cases where agents heavily edited or discarded AI replies to identify prompt gaps. Feed anonymized complaint patterns into monthly property review reports. The goal is not to make the AI handle complaints better — it is to reduce the complaints themselves by surfacing patterns that operations teams can act on before they become recurring issues.
