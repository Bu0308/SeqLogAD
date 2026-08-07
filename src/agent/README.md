# Agent

Contains the bounded, single-agent investigation workflow.

Input: anomaly IDs and service-layer tool contracts.

Output: investigation traces, verified hypotheses, test recommendations and incident reports.

Dependencies: LangGraph and a model provider are deferred until AGT-001/AGT-002.

Planned files: `state.py`, `graph.py`, `tracing.py` and read-only tools.

Safety boundary: no shell, production write or automatic remediation tool.

Implementation status: placeholder only; no model calls are made.
