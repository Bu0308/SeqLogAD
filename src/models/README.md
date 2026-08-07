# Models

Contains statistical, feature-based and neural sequence anomaly detector contracts.

Input: chronological `EventSequence` records.

Output: event-level and sequence-level anomaly scores, checkpoints and metadata.

Dependencies: scikit-learn for baselines and PyTorch for LSTM/Transformer phases. These are intentionally not installed in the Phase 1 scaffold.

Planned files: `statistical.py`, `isolation_forest.py`, `lstm_detector.py`, `transformer_detector.py`.

Implementation status: no model implementation, training or checkpoint exists.
