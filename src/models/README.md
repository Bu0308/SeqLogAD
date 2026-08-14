# Models

Planned V3 model boundary for statistical/LSTM baselines and heterogeneous experts A–C.

| Component | Role | Status |
|---|---|---|
| Frequency/statistical | Reference baseline | Not implemented |
| Markov/N-gram | Expert B: short transition surprise | Not implemented |
| Isolation Forest | Expert C: quantitative behavior | Not implemented |
| LSTM | Strong neural baseline | Not implemented |
| SeqLogAD-T | Expert A: long-range context/localization | Not implemented |

Inputs are leakage-safe `EventSequence` artifacts. Outputs must conform to the future `ExpertEvidence` schema. Training/checkpoint selection is human-owned; no model/checkpoint exists.

PyTorch/scikit-learn dependencies are not added by the V3 documentation task.
