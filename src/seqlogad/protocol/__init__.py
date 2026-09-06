"""Excel-roadmap Phase 1 protocol implementation (Bang_ke_hoach_SeqLogAD.xlsx).

Modules in this package implement P1.1-P1.8 of the authoritative workbook:

===========  ==========================================================
``schema``   LOG-UNIFY-001 canonical multi-source record contract (P1.3)
``nul``      ``seqlogad-nul-escape-v1`` byte-safety codec (P1.3 / P1.4)
``normalizer`` NORM-CS-001 deterministic masking normaliser (P1.4)
``architectures`` per-architecture raw adapters and the fold-role registry
``registry`` DATA-REG-001 dataset registry builder/validator (P1.2)
``chronology`` label-blind chronological unit index per architecture
``folds``    CS-SPLIT-001 leave-one-architecture-out folds (P1.5)
``buffer``   ADAPT-INPUT-001 target burn-in buffer contract (P1.6)
``labels``   evaluation-only label boundary (target labels never leak)
``audit``    LEAK-CS-001 isolation and leakage audit (P1.7)
``freeze``   G0 receipt and artifact freeze (P1.8)
===========  ==========================================================
"""

PROTOCOL_PLAN = "Bang_ke_hoach_SeqLogAD.xlsx"
PROTOCOL_ID = "DOMAIN-ADAPTIVE-FUSION-001"
PROTOCOL_VERSION = "2.0"
PHASE = "P1"
