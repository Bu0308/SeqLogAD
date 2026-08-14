# Retrieval

Planned Expert D compares observed event sequences with normal references fitted only from `BASE_TRAIN`.

P0 structural methods: edit distance, LCS, event n-gram overlap, and transition overlap. Expected output includes nearest-normal IDs, scores/distances, and coordinate-aware structural differences.

Dense semantic retrieval and generic BM25/hybrid knowledge retrieval are P1/downstream unless later evidence changes scope. No index or retrieval implementation exists.
