"""Bounded batched encoding shared by Sequence training and audit tests."""
import json
from .objective import _prompt, literal_text, encode_window


def _cached_batch_encode(tokenizer, texts, cache):
    missing = list(dict.fromkeys(text for text in texts if text not in cache))
    if missing:
        encoded = tokenizer(
            missing, add_special_tokens=False, padding=False, truncation=False,
        )["input_ids"]
        cache.update((text, tuple(ids)) for text, ids in zip(missing, encoded, strict=True))
    return [cache[text] for text in texts]


def _overflow_example(tokenizer, state, prompt_tokens, target_tokens, context_length):
    complete = state["keep"] == len(state["target_words"])
    suffix = list(target_tokens) + ([tokenizer.eos_token_id] if complete else [])
    prefix = [tokenizer.bos_token_id] + list(prompt_tokens)
    ids = prefix + suffix
    if len(ids) > context_length:
        return None, len(ids) - context_length
    return {
        "input_ids": ids,
        "attention_mask": [1] * len(ids),
        "labels": [-100] * len(prefix) + suffix,
        "coverage": state["keep"] / len(state["target_words"]),
        "retained_target_words": state["keep"],
        "original_target_words": len(state["target_words"]),
        "retained_context_records": len(state["contexts"]),
        "original_context_records": state["original_context"],
        "complete": complete and len(state["contexts"]) == state["original_context"],
    }, 0


def _encode_overflow_batch(tokenizer, pending, cfg, label, prompt_cache, target_cache):
    states = [{
        "position": position,
        "contexts": list(contexts),
        "original_context": len(contexts),
        "target_words": list(target_words),
        "keep": len(target_words),
    } for position, contexts, target_words in pending]
    resolved, failures, round_index = {}, {}, 0
    while states:
        round_index += 1
        prompt_texts = [_prompt(state["contexts"]) for state in states]
        target_texts = [" ".join(state["target_words"][:state["keep"]]) for state in states]
        prompts = _cached_batch_encode(tokenizer, prompt_texts, prompt_cache)
        targets = _cached_batch_encode(tokenizer, target_texts, target_cache)
        remaining = []
        for state, prompt_tokens, target_tokens in zip(states, prompts, targets, strict=True):
            example, overflow = _overflow_example(
                tokenizer, state, prompt_tokens, target_tokens, cfg["context_length"]
            )
            if example is not None:
                resolved[state["position"]] = example
                continue
            if len(state["contexts"]) > 1:
                state["contexts"] = state["contexts"][1:]
                state["keep"] = len(state["target_words"])
                remaining.append(state)
                continue
            state["keep"] -= max(1, overflow // 4)
            if state["keep"] > 0:
                remaining.append(state)
            else:
                failures[state["position"]] = "no causal context plus target content fits token horizon"
        states = remaining
        if round_index == 1 or round_index % 8 == 0:
            print(json.dumps({
                "encoding": label, "phase": "overflow_crop", "round": round_index,
                "active": len(states), "resolved": len(resolved), "rejected": len(failures),
            }), flush=True)
    return resolved, failures


def encoded_windows(rows, tokenizer, cfg, label="windows", batch_size=512):
    encoded, rejected = [], []
    fast_path = callable(tokenizer)
    prepared = []
    for row in rows:
        contexts = [message for message in row["context_messages"]
                    if message and message.strip()]
        target_words = literal_text(row["target_message"]).split()
        if not contexts or not target_words:
            reason = ("sequence window has no usable predecessor" if not contexts
                      else "sequence target is empty")
            rejected.append({"architecture_id": row["architecture_id"],
                             "window_id": row["window_id"], "reason": reason})
            continue
        prepared.append((row, contexts, " ".join(target_words)))

    for start in range(0, len(prepared), batch_size):
        chunk = prepared[start:start + batch_size]
        prompt_cache, target_cache = {}, {}
        if fast_path:
            prompt_texts = [_prompt(contexts) for _, contexts, _ in chunk]
            target_texts = [target for _, _, target in chunk]
            prompt_ids = _cached_batch_encode(tokenizer, prompt_texts, prompt_cache)
            target_ids = _cached_batch_encode(tokenizer, target_texts, target_cache)
        else:
            prompt_ids = [tokenizer.encode(_prompt(contexts), add_special_tokens=False)
                          for _, contexts, _ in chunk]
            target_ids = [tokenizer.encode(target, add_special_tokens=False)
                          for _, _, target in chunk]
        results, pending = [None] * len(chunk), []
        for position, ((row, contexts, target), prompt_tokens, target_tokens) in enumerate(zip(
                chunk, prompt_ids, target_ids, strict=True)):
            ids = [tokenizer.bos_token_id] + list(prompt_tokens) + list(target_tokens) + [tokenizer.eos_token_id]
            if len(ids) <= cfg["context_length"]:
                results[position] = {
                    "input_ids": ids,
                    "attention_mask": [1] * len(ids),
                    "labels": [-100] * (1 + len(prompt_tokens))
                              + list(target_tokens) + [tokenizer.eos_token_id],
                    "coverage": 1.0,
                    "retained_target_words": len(target.split()),
                    "original_target_words": len(target.split()),
                    "retained_context_records": len(contexts),
                    "original_context_records": len(contexts),
                    "complete": True,
                }
            elif fast_path:
                pending.append((position, contexts, target.split()))
            else:
                try:
                    results[position] = encode_window(
                        tokenizer, row["context_messages"], row["target_message"], cfg
                    )
                except ValueError as exc:
                    results[position] = str(exc)
        failures = {}
        if pending:
            resolved, failures = _encode_overflow_batch(
                tokenizer, pending, cfg, label, prompt_cache, target_cache
            )
            for position, example in resolved.items():
                results[position] = example
        for position, ((row, _, _), example) in enumerate(zip(chunk, results, strict=True)):
            if position in failures or isinstance(example, str):
                rejected.append({
                    "architecture_id": row["architecture_id"], "window_id": row["window_id"],
                    "reason": failures.get(position, example),
                })
                continue
            if example is None:
                raise RuntimeError("P2.2 batch encoder left an unresolved window")
            example.update(
                architecture_id=row["architecture_id"], window_id=row["window_id"],
                context_ranks=list(row["context_ranks"]), target_rank=row["target_rank"],
            )
            encoded.append(example)
        print(json.dumps({"encoding": label, "completed": min(start + len(chunk), len(prepared)),
                          "total": len(prepared), "rejected": len(rejected)}), flush=True)
    if not encoded:
        raise ValueError("all P2.2 windows abstained")
    return encoded, rejected


