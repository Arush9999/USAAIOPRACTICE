"""Deterministic, syllabus-aware multiple-choice question generation."""

from __future__ import annotations

import math
import random


COUNTS = {"easy": 50, "medium": 100, "hard": 50}
LEVEL_CODE = {"easy": "E", "medium": "M", "hard": "H"}
UNOFFICIAL = "Unofficial practice: "


def _rng(slug: str, difficulty: str, index: int) -> random.Random:
    seed = f"{slug}|{difficulty}|{index}"
    return random.Random(seed)


def _shuffle(rng: random.Random, answer: str, distractors: list[str]) -> tuple[list[str], str]:
    choices = []
    for choice in [
        answer,
        *distractors,
        "The result cannot be determined from the given information.",
        "The operation always returns zero.",
        "The operation is undefined.",
    ]:
        if choice not in choices:
            choices.append(choice)
        if len(choices) == 4:
            break
    rng.shuffle(choices)
    return choices, answer


def _numeric_question(
    rng: random.Random, title: str, summary: str, difficulty: str, index: int
) -> tuple[str, list[str], str, str, list[str]]:
    text = f"{title} {summary}".lower()
    a = rng.randint(2, 5) + (1 if difficulty == "hard" else 0)
    b = rng.randint(2, 6)
    c = rng.randint(2, 7)
    context = rng.choice(["a notebook experiment", "a model audit", "a training run", "a small worked example"])

    if any(word in text for word in ("attention", "query", "key", "head")):
        tokens, dk, dv = a + b, rng.choice([4, 9, 16, 25, 36, 64]), c + 1
        scale = int(math.sqrt(dk))
        prompt = (
            f"In {context}, Q and K each contain {tokens} tokens with key dimension {dk}, "
            f"and V has value dimension {dv}. What is the attention output shape and score divisor?"
        )
        answer = f"({tokens}, {dv}) and √{dk} = {scale}"
        choices, answer = _shuffle(rng, answer, [
            f"({tokens}, {tokens}) and {dk}",
            f"({dv}, {tokens}) and √{dv}",
            f"({tokens}, {dk}) and {scale * scale}",
        ])
        explanation = f"QKᵀ is {tokens}×{tokens}; row-wise softmax times V gives {tokens}×{dv}, and logits are divided by √d_k={scale}."
        hints = ["Write the shapes of QKᵀ and then (QKᵀ)V.", "The scaling uses the key dimension, not token count."]
    elif any(word in text for word in ("convolution", "kernel", "padding", "stride", "pool", "receptive")):
        width, kernel, padding, stride = 12 + 2 * a, 3, rng.choice([0, 1]), rng.choice([1, 2])
        out = (width + 2 * padding - kernel) // stride + 1
        prompt = f"A 1D spatial axis has width {width}; a kernel of {kernel}, padding {padding}, and stride {stride} is applied. What output width results?"
        answer = str(out)
        choices, answer = _shuffle(rng, answer, [str(out + 1), str(max(1, out - 1)), str(width * kernel)])
        explanation = f"Use floor((W+2p-k)/s)+1: floor(({width}+{2*padding}-{kernel})/{stride})+1={out}."
        hints = ["Substitute into floor((W + 2p - k) / s) + 1."]
    elif any(word in text for word in ("probability", "bayes", "expectation", "variance", "distribution")):
        successes, total = a, a + b + c
        p = successes / total
        prompt = f"In {context}, {successes} of {total} equally likely outcomes satisfy event A. What is P(A)?"
        answer = f"{successes}/{total}"
        choices, answer = _shuffle(rng, answer, [f"{total-successes}/{total}", f"{successes}/{total-successes}", f"1/{total}"])
        explanation = f"Probability under equally likely outcomes is favorable/total, so P(A)={successes}/{total}≈{p:.3f}."
        hints = ["Count favorable outcomes and divide by all outcomes."]
    elif any(word in text for word in ("iou", "dice", "precision", "recall", "metric", "evaluation")):
        intersection, left, right = a, a + b, a + c
        union = left + right - intersection
        prompt = f"Two predicted/target sets have sizes {left} and {right}, with intersection {intersection}. What is their IoU?"
        answer = f"{intersection}/{union}"
        choices, answer = _shuffle(rng, answer, [f"{2*intersection}/{left+right}", f"{intersection}/{left+right}", f"{union}/{intersection}"])
        explanation = f"IoU is intersection/union, and union={left}+{right}-{intersection}={union}, giving {intersection}/{union}."
        hints = ["Union adds both set sizes and subtracts the overlap once."]
    elif any(word in text for word in ("gradient", "optimization", "learning rate", "descent", "derivative")):
        theta, grad = 2 * a, b
        eta = rng.choice([0.1, 0.2, 0.5])
        updated = theta - eta * grad
        prompt = f"A scalar parameter is θ={theta}, its gradient is {grad}, and gradient descent uses η={eta}. What is the next θ?"
        answer = f"{updated:g}"
        choices, answer = _shuffle(rng, answer, [f"{theta+eta*grad:g}", f"{theta-grad:g}", f"{eta*grad:g}"])
        explanation = f"Gradient descent subtracts η∇L: {theta}-{eta}·{grad}={updated:g}."
        hints = ["Use θ_next = θ - ηg.", "A positive gradient makes a descent update smaller."]
    elif any(word in text for word in ("shape", "matrix", "array", "linear", "affine", "embedding", "latent", "tensor", "pca", "svd")):
        m, k, n = a + 2, b + 1, c + 2
        prompt = f"In {context}, A has shape ({m}, {k}) and B has shape ({k}, {n}). What is the shape of AB?"
        answer = f"({m}, {n})"
        choices, answer = _shuffle(rng, answer, [f"({k}, {k})", f"({n}, {m})", f"({m}, {k})"])
        explanation = f"The inner dimensions {k} match and disappear; the outer dimensions remain, so AB is {m}×{n}."
        hints = ["For (m×k)(k×n), retain the two outer dimensions."]
    else:
        samples, correct = 10 * (a + b), 10 * a
        accuracy = 100 * correct / samples
        prompt = f"A {title.lower()} check gets {correct} of {samples} cases correct. What percentage is correct?"
        answer = f"{accuracy:g}%"
        choices, answer = _shuffle(rng, answer, [f"{100-accuracy:g}%", f"{correct/samples:g}%", f"{samples/correct:g}%"])
        explanation = f"Percentage correct is 100·{correct}/{samples}={accuracy:g}%."
        hints = ["Divide correct cases by total cases, then multiply by 100."]
    return prompt, choices, answer, UNOFFICIAL + explanation, hints


def _concept_question(
    rng: random.Random, title: str, summary: str, difficulty: str, index: int
) -> tuple[str, list[str], str, str, list[str]]:
    stems = {
        "easy": ["Which statement best describes", "Which choice is most consistent with", "What is the best first principle for"],
        "medium": ["A student is checking a solution about", "Which diagnostic is most useful when applying", "Which claim is defensible about"],
        "hard": ["Before accepting a subtle result about", "Which argument is strongest for", "In an unfamiliar case involving"],
    }
    lead = rng.choice(stems[difficulty])
    focus = summary.rstrip(".")
    prompt = f"{lead} {title.lower()}? (Variant {index + 1})"
    answer = f"Use the defining objective, assumptions, and dimensions: {focus}."
    distractors = [
        "Choose the method only because it has the most parameters; assumptions and outputs do not matter.",
        "If code executes without an exception, its mathematics and evaluation are necessarily correct.",
        "Fit preprocessing and tune choices on the final test set so every available label influences training.",
    ]
    if difficulty == "hard":
        distractors[0] = "Rely on a memorized formula even when its input dimensions or information constraints differ."
    choices, answer = _shuffle(rng, answer, distractors)
    explanation = UNOFFICIAL + f"The sound choice explicitly checks the purpose and constraints of {title}: {focus}. The alternatives confuse execution or model size with validity, or leak evaluation information."
    hints = ["Reject claims that ignore assumptions, tensor dimensions, or held-out evaluation.", f"Recall the core scope: {focus}."]
    return prompt, choices, answer, explanation, hints


def generate_questions(
    *,
    topic_slug: str,
    topic_code: str,
    subtopic_slug: str,
    subtopic_code: str,
    title: str,
    summary: str,
) -> list[dict]:
    """Generate exactly 200 deterministic MCQs for one subtopic."""
    rows: list[dict] = []
    for difficulty, count in COUNTS.items():
        for index in range(count):
            rng = _rng(subtopic_slug, difficulty, index)
            # Numerical work becomes more frequent as difficulty rises while
            # every level retains conceptual retrieval and misconception checks.
            numerical = (index % {"easy": 4, "medium": 2, "hard": 2}[difficulty]) == 0
            make = _numeric_question if numerical else _concept_question
            prompt, choices, answer, explanation, hints = make(rng, title, summary, difficulty, index)
            prompt = f"{title} practice case {index + 1} ({difficulty}): {prompt}"
            tags = [subtopic_slug]
            if difficulty == "easy" and index < 5:
                tags.append("learn-check")
            rows.append({
                "public_id": f"{topic_code}-{subtopic_code}-{LEVEL_CODE[difficulty]}-{index + 1:04d}",
                "qtype": "multiple_choice",
                "difficulty": difficulty,
                "prompt": prompt,
                "answer": answer,
                "explanation": explanation,
                "hints": hints[: rng.randint(1, 2)],
                "choices": choices,
                "tags": ",".join(tags),
                "available": True,
            })
    return rows
