# Models

Planned v1.1 boundary for the smallest methods needed to test sequence added value.

| Component | Role | Status |
|---|---|---|
| Unseen event / length / count vector | MUST order-insensitive controls | Not implemented |
| Markov/N-gram | MUST minimal sequential comparator | Not implemented |
| Isolation Forest | MUST / required primary order-insensitive candidate under EFFECT-001 | Not implemented |
| SeqLogAD-T | CONDITIONAL after sequence-signal gate | Not implemented |
| LSTM | REMOVED_FROM_CORE historical placeholder | Not implemented |
| F0/F1 simple fusion | CONDITIONAL after measured complementarity | Not implemented |
| Retrieval/RAG/Agent | FUTURE; outside detector core | Placeholder only |

Inputs must be leakage-safe `EventSequence` artifacts. Human owns empirical execution/selection; no estimator, checkpoint, prediction, or metric exists.

Isolation Forest is stochastic and must use seeds `42`, `43`, and `44`. The
unseen-event, length, count/count-vector, and count-fitted Markov/N-gram controls
are deterministic and must not receive fabricated repeated seed runs. Selection
is validation-only; TEST remains sealed.

Future dependencies are added only by the owning approved method task.
