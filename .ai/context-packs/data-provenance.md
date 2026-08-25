# Data-provenance context pack

## READ BY DEFAULT
[`../../configs/active-state.yaml`](../../configs/active-state.yaml), [`../../docs/dataset-acquisition.md`](../../docs/dataset-acquisition.md), [`../../docs/split-artifacts-and-test-seal.md`](../../docs/split-artifacts-and-test-seal.md), [`../../docs/parser-fit-and-freeze.md`](../../docs/parser-fit-and-freeze.md).

## READ IF NEEDED
[`../../docs/metadata-extraction-contract.md`](../../docs/metadata-extraction-contract.md), [`../../docs/split-clarification-contract.md`](../../docs/split-clarification-contract.md), dataset cards, schema contracts, and cited implementation tests.

## AVOID BY DEFAULT
Raw data content, sealed TEST membership, ignored generated artifacts not explicitly assigned, and historical split/parser rules.

## AUTHORITATIVE CONTRACTS
Protocol v1.1; split clarification; purge decision; active dataset/split/parser hashes in active state.

## EXPECTED OUTPUT
Identity/hash lineage, label-access statement, leakage boundary, determinism evidence, and no scientific interpretation.

## ESCALATION CONDITIONS
Fingerprint/hash mismatch, missing artifact, label use outside contract, parser mutation/refit, split change, or any TEST exposure.
