# RAG — Future Only

This module is outside the Research Freeze v1.1 core. The text below describes a possible downstream boundary, not active work.

Prepares knowledge-base items, evidence records, hypotheses and model-provider contracts.

Input: anomaly context, retrieved items, documentation and test cases.

Output: validated evidence-grounded hypotheses and incident-report context.

Dependencies: Pydantic now; model provider libraries are deferred until RAG-003.

Planned files: `kb_builder.py`, `schemas.py`, `verifier.py`, `model_provider.py`.

Implementation status: not started; no dependency or scientific claim is active.
