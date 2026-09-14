"""Post-training synthetic semantic probes; never training or checkpoint-selection data."""
PAIRS = [
    ('semantic_change', 'disk write completed successfully', 'disk write failed permission denied'),
    ('format_change', 'disk write completed successfully', '  disk   write completed successfully  '),
    ('oov', 'service worker connected', 'service zxqv_unseen_worker connected'),
]


def run_probes(score):
    """Score callback takes text; differences are observations, not accuracy metrics."""
    results = []
    for kind, left, right in PAIRS:
        a, b = score(left), score(right)
        results.append({'kind': kind, 'left': a, 'right': b,
                        'delta': None if a['score_raw'] is None or b['score_raw'] is None
                        else b['score_raw'] - a['score_raw']})
    return {'scope': 'SYNTHETIC_DIAGNOSTIC_ONLY', 'used_for_training_or_selection': False,
            'natural_anomaly_performance': None, 'results': results}
