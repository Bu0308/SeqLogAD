# RAG

Prepares knowledge-base items, evidence records, hypotheses and model-provider contracts.

Input: anomaly context, retrieved items, documentation and test cases.

Output: validated evidence-grounded hypotheses and incident-report context.

Dependencies: Pydantic now; model provider libraries are deferred until RAG-003.

Planned files: `kb_builder.py`, `schemas.py`, `verifier.py`, `model_provider.py`.

Implementation status: schema and verifier implementation have not started.
