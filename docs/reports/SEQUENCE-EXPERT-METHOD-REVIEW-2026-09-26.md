# Sequence Expert V12 — method review and implementation choices

Reviewed 2026-09-26. The figure is
[Sequence Expert V12](../architecture/sequence-expert-v12.svg). These papers
motivate candidate designs; their reported F1 scores are not evidence of
SeqLogAD performance under its held-out protocol.

| Primary source | What the authors train | Fit for current SeqLogAD protocol |
| --- | --- | --- |
| [DeepLog (CCS 2017)](https://nlp.cs.utah.edu/assets/pdfs/du2017deeplog.pdf) | LSTM predicts the next log key from recent keys. | Establishes the next-event forecasting baseline; our target is normalized message-token NLL, so raw losses are not directly comparable. |
| [LogSD (FSE 2024)](https://dl.acm.org/doi/10.1145/3660800) | Two self-supervised subnets, frequency-aware masking and reconstruction on historical normal data. | Frequency bias is a useful hypothesis. Current source data have no verified normal-only status, so its normal-only training assumption is not adopted. |
| [TLAN (Sensors 2024)](https://www.mdpi.com/1424-8220/24/24/7949) | Multiple temporal receptive fields and logical attention over log sequences. | Motivates testing more than one context scale. V12 uses causal suffix lengths 1/2/4/full as a distinct, label-free input augmentation, not TLAN's network. |
| [rsLoRA (2023)](https://arxiv.org/abs/2312.03732) and [PEFT API](https://huggingface.co/docs/peft/package_reference/lora) | Adapter scaling by alpha/sqrt(rank), instead of alpha/rank. | Implemented as `use_rslora=True` with an isolated V12 checkpoint identity. It is an optimization hypothesis, not an assured anomaly F1 gain. |
| [PEFT for log anomalies (PAKDD 2025)](https://arxiv.org/html/2503.08045) | Llama/RoBERTa/GPT-2 with LoRA or ReFT and a supervised anomaly classifier. | Shows relevant PEFT alternatives, but its train set has normal/anomaly labels. We do not import its ReFT classifier or compare its F1 to our label-free source NLL. |
| [ContraLog (2026 preprint)](https://arxiv.org/abs/2602.03678) | Parser-free message and sequence encoders; masked embedding prediction plus contrastive learning. | Strong separate lightweight/hierarchical candidate for P3.2. Mixing its bidirectional masked objective into V12 would change the causal target and budget. |
| [ParseRobustLog (2026)](https://doi.org/10.4018/IJWSR.406287) | Routes among LSTM, GRU, TCN and Transformer experts, with template-supervised contrastive encoding. | Suggests a later efficiency comparator. Its template supervision and additional experts do not fit the current single-adapter, source-only V12 budget. |

## V12 change and metric contract

- Frozen Llama-3.1-8B in 4-bit NF4 with a separate rank-16 rsLoRA `sequence`
  adapter on q/k/v/o projections.
- Source-train windows are sampled evenly by source. Every target remains the
  same; a training view uses the full predecessor chain half the time and a
  causal suffix of 1, 2 or 4 records otherwise. Validation/inference retain
  the full available context. No anomaly labels or target data enter training.
- Model loss, checkpoint selection and early stopping remain next-log target
  NLL. Log per-source NLL and perplexity, context-view counts, target/context
  coverage, numerical checks, runtime and VRAM.
- The researcher confirmed no authorized labeled development validation set
  exists. Thus natural F1, precision, recall, AUROC and AP remain null until a
  labeled evaluation gate with frozen unit and threshold is available. Test
  labels cannot be used to choose a checkpoint.
- V11 remains an immutable packaged reference. Compare V11 and V12 on the
  same source-validation folds and budget before claiming a better candidate.
  The expected GPU runtime is unknown until measured.

## Projmem capture

The V12 RunPod kit includes a pinned Projmem 0.4.0a1 wheel from commit
`d684d7d172792344c4d31f9ec74067a23cc023e3`. Each notebook execution
initializes Projmem on the Network Volume and wraps the complete trainer with
`pmem run`. Its `.pmem/pmem.db`, per-attempt portability export and final
scientific ZIP must be collected together. Failures remain recorded even if
the scientific ZIP is absent.
