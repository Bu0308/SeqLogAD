# Architecture documentation

The forward v2 architecture is maintained in [`../../Plan/master-implementation-plan-v2-domain-adaptive-fusion.md`](../../Plan/master-implementation-plan-v2-domain-adaptive-fusion.md) and [`../research-protocol-v2-domain-adaptive-fusion.md`](../research-protocol-v2-domain-adaptive-fusion.md). The v1.1 dataset integrity/provenance, schema contracts, real raw split/TEST guards, and normal-only Drain3 fit/freeze remain preserved foundation artifacts.

The v2 fixed stack is two independent LoRA adapters on a frozen Llama-3.1-8B base plus GTAT, with target-normal calibration and adaptive fusion. Retrieval/RAG/Agent/API/UI/Elasticsearch remain outside the detector core.
