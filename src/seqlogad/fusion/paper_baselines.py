"""Re-implemented published log-AD baselines under the SeqLogAD protocol.

Every baseline is fitted label-free on the same SOURCE_TRAIN windows the LLM
experts saw, and scores the same evaluation windows, so AP/AUROC are directly
comparable (unlike numbers copied from papers with other splits/thresholds).

* PCA residual (Xu et al., SOSP 2009): TF-IDF count vectors of the window,
  squared prediction error outside the top components (95 % variance).
* Isolation Forest (Liu et al., ICDM 2008) on the same count vectors.  Known
  limitation: a template unseen in training is a constant-zero feature during
  fitting, so the forest never splits on it (novel-template anomalies invisible).
* DeepLog (Du et al., CCS 2017): LSTM over template ids of the <= 8 predecessors
  predicting the next template; score = -log p(observed next template), the
  continuous form of DeepLog's top-g rule.
* TF-IDF kNN novelty (K4-style, arXiv 2507.20051): 1 - max cosine similarity of
  the target message to the training messages.
"""
from __future__ import annotations

from collections import Counter

import numpy as np

OOV = 0


class Vocab:
    def __init__(self, messages, size: int = 2000):
        common = [m for m, _ in Counter(messages).most_common(size - 1)]
        self.index = {m: i + 1 for i, m in enumerate(common)}

    def __len__(self):
        return len(self.index) + 1

    def ids(self, messages):
        return [self.index.get(m, OOV) for m in messages]


def count_matrix(windows, vocab: Vocab) -> np.ndarray:
    out = np.zeros((len(windows), len(vocab)), dtype=np.float32)
    for row, (context, target) in enumerate(windows):
        for i in vocab.ids(list(context) + [target]):
            out[row, i] += 1.0
    return out


def tfidf_fit(train: np.ndarray):
    df = (train > 0).sum(0)
    return np.log((1 + train.shape[0]) / (1 + df)) + 1.0


def pca_scores(train: np.ndarray, test: np.ndarray, variance: float = 0.95) -> np.ndarray:
    idf = tfidf_fit(train)
    a, b = train * idf, test * idf
    mean = a.mean(0)
    _, s, vt = np.linalg.svd(a - mean, full_matrices=False)
    k = int(np.searchsorted(np.cumsum(s ** 2) / np.sum(s ** 2), variance) + 1)
    p = vt[:k]
    centred = b - mean
    residual = centred - centred @ p.T @ p
    return np.einsum("ij,ij->i", residual, residual)


def iforest_scores(train: np.ndarray, test: np.ndarray, seed: int = 42) -> np.ndarray:
    from sklearn.ensemble import IsolationForest

    model = IsolationForest(n_estimators=200, random_state=seed).fit(train)
    return -model.score_samples(test)


def knn_tfidf_scores(train_messages, test_messages) -> np.ndarray:
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizer = TfidfVectorizer(token_pattern=r"[^\s]+", min_df=1)
    unique = sorted(set(train_messages))
    reference = vectorizer.fit_transform(unique)
    query = vectorizer.transform(test_messages)
    best = np.zeros(query.shape[0])
    for start in range(0, query.shape[0], 512):
        sims = (query[start:start + 512] @ reference.T).toarray()
        best[start:start + 512] = sims.max(1) if sims.size else 0.0
    return 1.0 - best


def deeplog_scores(train_windows, test_windows, vocab: Vocab, *, epochs: int = 5, seed: int = 42,
                   device: str | None = None) -> np.ndarray:
    import torch
    from torch import nn

    torch.manual_seed(seed)
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def tensors(windows):
        ctx = np.zeros((len(windows), 8), dtype=np.int64)
        for row, (context, _) in enumerate(windows):
            ids = vocab.ids(list(context)[-8:])
            ctx[row, 8 - len(ids):] = ids
        tgt = np.array([vocab.ids([t])[0] for _, t in windows], dtype=np.int64)
        return torch.tensor(ctx), torch.tensor(tgt)

    class Model(nn.Module):
        def __init__(self, n):
            super().__init__()
            self.embed = nn.Embedding(n, 64)
            self.lstm = nn.LSTM(64, 64, num_layers=2, batch_first=True)
            self.out = nn.Linear(64, n)

        def forward(self, x):
            h, _ = self.lstm(self.embed(x))
            return self.out(h[:, -1])

    x, y = tensors(train_windows)
    model = Model(len(vocab)).to(device)
    optim = torch.optim.Adam(model.parameters(), lr=1e-3)
    generator = torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        order = torch.randperm(len(x), generator=generator)
        for start in range(0, len(x), 256):
            idx = order[start:start + 256]
            loss = nn.functional.cross_entropy(model(x[idx].to(device)), y[idx].to(device))
            optim.zero_grad()
            loss.backward()
            optim.step()
    model.eval()
    tx, ty = tensors(test_windows)
    scores = []
    with torch.no_grad():
        for start in range(0, len(tx), 1024):
            logp = torch.log_softmax(model(tx[start:start + 1024].to(device)), -1)
            scores.append(-logp.gather(1, ty[start:start + 1024].to(device)[:, None])[:, 0].cpu().numpy())
    return np.concatenate(scores)


def all_baselines(train_windows, test_windows, *, seed: int = 42) -> dict[str, np.ndarray]:
    """train_windows/test_windows: lists of (context_messages, target_message)."""
    vocab = Vocab([m for c, t in train_windows for m in [*c, t]])
    train_counts, test_counts = count_matrix(train_windows, vocab), count_matrix(test_windows, vocab)
    return {
        "pca_xu2009": pca_scores(train_counts, test_counts),
        "iforest_liu2008": iforest_scores(train_counts, test_counts, seed),
        "deeplog_du2017": deeplog_scores(train_windows, test_windows, vocab, seed=seed),
        "knn_tfidf_k4": knn_tfidf_scores([t for _, t in train_windows], [t for _, t in test_windows]),
    }
