# Models

Planned v1.1 boundary for the smallest methods needed to test sequence added value.

| Component | Role | Status |
|---|---|---|
| Unseen event / length / count vector | MUST order-insensitive controls | Not implemented |
| Markov/N-gram | MUST minimal sequential comparator | Not implemented |
| Isolation Forest | SHOULD order-insensitive comparator | Not implemented |
| SeqLogAD-T | CONDITIONAL after sequence-signal gate | Not implemented |
| LSTM | REMOVED_FROM_CORE historical placeholder | Not implemented |

Inputs must be leakage-safe `EventSequence` artifacts. Human owns empirical execution/selection; no estimator, checkpoint, prediction, or metric exists.

Future dependencies are added only by the owning approved method task.
