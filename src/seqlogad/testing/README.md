# Testing recommendation

Transforms an anomaly, observed/expected sequence, verified hypothesis and retrieved documentation into a structured test recommendation.

Input: investigation context and evidence IDs.

Output: title, objective, preconditions, steps, expected result, priority, type and related evidence.

Dependencies: Pydantic; model-provider integration is deferred.

Planned files: `recommendation.py`, optional `skeleton.py` and `validator.py`.

Implementation status: structured recommendation is P0; code skeleton generation is P1/P2.
