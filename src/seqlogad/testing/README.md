# Test recommendation — Future Only

This former downstream differentiation is outside the v1.1 scientific core.

Transforms an anomaly, observed/expected sequence, verified hypothesis and retrieved documentation into a structured test recommendation.

Input: investigation context and evidence IDs.

Output: title, objective, preconditions, steps, expected result, priority, type and related evidence.

Dependencies: Pydantic; model-provider integration is deferred.

Planned files: `recommendation.py`, optional `skeleton.py` and `validator.py`.

Implementation status: future, not started. Reactivation requires a separate scope decision after the detector study.
