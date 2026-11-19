"""Offline evaluators: static checks + trajectory / final-answer LLM judges."""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from dataset_io import question_from_inputs
from mila_agent.graph import _build_llm

# Static floor for a non-empty assistant reply (override with EVAL_MIN_ANSWER_CHARS).
DEFAULT_MIN_ANSWER_CHARS = 20


def _as_mapping(obj: Any) -> dict[str, Any]:
    """LangSmith may pass dicts or pydantic Example/Run objects."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {
        "inputs": getattr(obj, "inputs", None) or {},
        "outputs": getattr(obj, "outputs", None) or {},
    }


def _tool_names(trajectory: list[dict[str, Any]] | None) -> list[str]:
    if not trajectory:
        return []
    return [str(step.get("tool") or "") for step in trajectory]


def _pass_fail_score(text: str) -> tuple[float, str]:
    upper = text.upper()
    if "FAIL" in upper and upper.strip().startswith("FAIL"):
        return 0.0, text[:200]
    if "PASS" in upper:
        return 1.0, text[:200]
    return 0.0, text[:200]


def answer_min_chars(run: Any, example: Any) -> dict[str, Any]:
    """
    Static check: assistant answer length >= EVAL_MIN_ANSWER_CHARS (default 20).
    Score 1.0 if long enough, else 0.0.
    """
    del example  # unused; signature matches LangSmith evaluators
    run_map = _as_mapping(run)
    answer = str((run_map.get("outputs") or {}).get("answer") or "")
    minimum = int(os.environ.get("EVAL_MIN_ANSWER_CHARS", DEFAULT_MIN_ANSWER_CHARS))
    length = len(answer.strip())
    score = 1.0 if length >= minimum else 0.0
    return {
        "key": "answer_min_chars",
        "score": score,
        "comment": f"len={length} min={minimum}",
    }


def trajectory_subsequence(run: Any, example: Any) -> dict[str, Any]:
    """
    Static check: expected tool names appear in order as a subsequence of actual calls.
    Arg equality is best-effort for keys present on the expected step.
    """
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    expected = (example_map.get("outputs") or {}).get("trajectory") or []
    actual = (run_map.get("outputs") or {}).get("trajectory") or []
    exp_names = _tool_names(expected)
    act_names = _tool_names(actual)

    if not exp_names:
        score = 1.0 if not act_names else 0.0
        return {"key": "trajectory_subsequence", "score": score}

    i = 0
    for name in act_names:
        if i < len(exp_names) and name == exp_names[i]:
            i += 1
    name_ok = i == len(exp_names)

    args_ok = True
    if name_ok:
        j = 0
        for step in actual:
            if j >= len(expected):
                break
            if step.get("tool") != expected[j].get("tool"):
                continue
            exp_args = expected[j].get("args") or {}
            act_args = step.get("args") or {}
            for key, value in exp_args.items():
                if act_args.get(key) != value:
                    args_ok = False
                    break
            j += 1
            if not args_ok:
                break

    score = 1.0 if name_ok and args_ok else (0.5 if name_ok else 0.0)
    return {
        "key": "trajectory_subsequence",
        "score": score,
        "comment": f"expected={exp_names} actual={act_names}",
    }


def trajectory_llm_judge(run: Any, example: Any) -> dict[str, Any]:
    """LLM-as-judge: did tool calls match the expected trajectory / task?"""
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    expected = (example_map.get("outputs") or {}).get("trajectory") or []
    actual = (run_map.get("outputs") or {}).get("trajectory") or []
    reference = (example_map.get("outputs") or {}).get("reference") or ""
    try:
        question = question_from_inputs(example_map.get("inputs") or {})
    except ValueError:
        question = ""

    llm = _build_llm()
    verdict = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You grade a mila-assistant's tool-calling trajectory. "
                    "Reply with ONLY PASS or FAIL.\n"
                    "PASS if the tools called (names and key args) reasonably match the expected "
                    "trajectory for the question. Extra harmless tools may be OK; missing required "
                    "tools or wrong args are FAIL. Empty expected trajectory means no tools should run."
                )
            ),
            HumanMessage(
                content=(
                    f"Question: {question}\n"
                    f"Reference intent: {reference}\n"
                    f"Expected trajectory JSON: {json.dumps(expected)}\n"
                    f"Actual trajectory JSON: {json.dumps(actual)}\n"
                )
            ),
        ]
    )
    text = verdict.content if isinstance(verdict.content, str) else str(verdict.content)
    score, comment = _pass_fail_score(text)
    return {"key": "trajectory_llm_judge", "score": score, "comment": comment}


def _expect_polarity(example_map: dict[str, Any]) -> str:
    """positive | negative from metadata.expect (default positive)."""
    meta = example_map.get("metadata") or {}
    expect = str(meta.get("expect") or "positive").strip().lower()
    if expect in {"negative", "neg", "refuse", "reject"}:
        return "negative"
    return "positive"


def intent_satisfied(run: Any, example: Any) -> dict[str, Any]:
    """
    LLM-as-judge for intent success, polarity-aware via metadata.expect:
      positive — fulfill the knowledge request (tools + useful answer)
      negative — refuse / stay in scope (no retrieval tools when none expected)
    """
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    polarity = _expect_polarity(example_map)
    reference = (example_map.get("outputs") or {}).get("reference") or ""
    expected_traj = (example_map.get("outputs") or {}).get("trajectory") or []
    answer = (run_map.get("outputs") or {}).get("answer") or ""
    actual_traj = (run_map.get("outputs") or {}).get("trajectory") or []
    try:
        question = question_from_inputs(example_map.get("inputs") or {})
    except ValueError:
        question = ""

    if polarity == "negative":
        system = (
            "You grade a NEGATIVE test case for a mila assistant. "
            "Reply with ONLY PASS or FAIL.\n"
            "PASS if the assistant correctly refuses or stays out of scope "
            "(does not pretend to complete an off-topic task with retrieval tools).\n"
            "FAIL if it calls retrieval tools unnecessarily or fully answers as if it were a general assistant "
            "when the reference says it should decline."
        )
    else:
        system = (
            "You grade a POSITIVE test case for a mila assistant. "
            "Reply with ONLY PASS or FAIL.\n"
            "PASS if the assistant's tools and answer reasonably fulfill the user's knowledge "
            "request given the reference.\n"
            "FAIL if it refuses, misses the task, or produces an empty/wrong result."
        )

    llm = _build_llm()
    verdict = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(
                content=(
                    f"Expect polarity: {polarity}\n"
                    f"Question: {question}\n"
                    f"Reference intent: {reference}\n"
                    f"Expected trajectory JSON: {json.dumps(expected_traj)}\n"
                    f"Actual trajectory JSON: {json.dumps(actual_traj)}\n"
                    f"Assistant answer: {answer}\n"
                )
            ),
        ]
    )
    text = verdict.content if isinstance(verdict.content, str) else str(verdict.content)
    score, comment = _pass_fail_score(text)
    return {
        "key": "intent_satisfied",
        "score": score,
        "comment": f"expect={polarity}; {comment}",
    }


def final_response_judge(run: Any, example: Any) -> dict[str, Any]:
    """LLM-as-judge: does the final answer match the reference intent?"""
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    polarity = _expect_polarity(example_map)
    reference = (example_map.get("outputs") or {}).get("reference") or ""
    answer = (run_map.get("outputs") or {}).get("answer") or ""
    try:
        question = question_from_inputs(example_map.get("inputs") or {})
    except ValueError:
        question = ""

    if polarity == "negative":
        system = (
            "You grade a NEGATIVE-case reply. Reply with ONLY PASS or FAIL.\n"
            "PASS if the answer declines or stays scoped to accessible knowledge (per reference).\n"
            "FAIL if it fully answers the off-topic question as a general assistant."
        )
    else:
        system = (
            "You grade a POSITIVE-case reply. Reply with ONLY PASS or FAIL.\n"
            "PASS if the answer reasonably satisfies the user question given the reference intent.\n"
            "FAIL if it is wrong, empty, refuses, or ignores the task."
        )

    llm = _build_llm()
    verdict = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(
                content=(
                    f"Expect polarity: {polarity}\n"
                    f"Question: {question}\n"
                    f"Reference intent: {reference}\n"
                    f"Assistant answer: {answer}\n"
                )
            ),
        ]
    )
    text = verdict.content if isinstance(verdict.content, str) else str(verdict.content)
    score, comment = _pass_fail_score(text)
    return {"key": "final_response_judge", "score": score, "comment": f"expect={polarity}; {comment}"}


# --- Mila deterministic checks (RBAC / PII) ---------------------------------------


def _example_meta(example_map: dict[str, Any]) -> dict[str, Any]:
    return dict(example_map.get("metadata") or {})


def _run_outputs(run_map: dict[str, Any]) -> dict[str, Any]:
    return dict(run_map.get("outputs") or {})


def _retrieve_hits(run_map: dict[str, Any]) -> list[dict[str, Any]]:
    retrieve = _run_outputs(run_map).get("retrieve") or {}
    hits = retrieve.get("hits") if isinstance(retrieve, dict) else None
    return [h for h in (hits or []) if isinstance(h, dict)]


def _caller_role(example_map: dict[str, Any]) -> str:
    """Role used for search: incognito → public; else inputs.caller / metadata."""
    from mila_agent.access_policy import normalize_role

    inputs = example_map.get("inputs") or {}
    caller = inputs.get("caller") if isinstance(inputs, dict) else None
    meta = _example_meta(example_map)
    auth_mode = ""
    role = ""
    if isinstance(caller, dict):
        auth_mode = str(caller.get("auth_mode") or "")
        role = str(caller.get("role") or "")
    auth_mode = auth_mode or str(meta.get("auth_mode") or "")
    role = role or str(meta.get("role") or "employee")
    if auth_mode.strip().lower() == "incognito":
        return "public"
    return normalize_role(role)


def rbac_hits_allowed(run: Any, example: Any) -> dict[str, Any]:
    """
    Deterministic: every retrieved hit must pass ``document_allowed`` for the
    caller role (same algo as production RBAC). Skips when no hits / no retrieve.
    """
    from mila_agent.access_policy import document_allowed

    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    hits = _retrieve_hits(run_map)
    if not hits:
        return {
            "key": "rbac_hits_allowed",
            "score": 1.0,
            "comment": "skipped: no retrieve hits",
        }

    role = _caller_role(example_map)
    bad: list[str] = []
    for hit in hits:
        audience = str(hit.get("intended_audience") or "")
        sensitivity = str(hit.get("sensitivity") or "")
        if not document_allowed(
            role,
            intended_audience=audience,
            sensitivity=sensitivity,
        ):
            bad.append(f"{hit.get('doc_id')}({audience}/{sensitivity})")

    score = 1.0 if not bad else 0.0
    return {
        "key": "rbac_hits_allowed",
        "score": score,
        "comment": f"role={role} bad={bad or 'none'} n={len(hits)}",
    }


def rbac_dataset_docs(run: Any, example: Any) -> dict[str, Any]:
    """
    Deterministic: dataset-hardcoded doc expectations.

    metadata.forbidden_doc_ids — must not appear in retrieve hits
    metadata.required_doc_ids — at least one must appear (when retrieve ran with hits
      expected; if required is set and hits empty → fail)
    metadata.answer_must_not_contain — substrings that must not appear in the answer
    """
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    meta = _example_meta(example_map)
    forbidden = [str(x) for x in (meta.get("forbidden_doc_ids") or [])]
    required = [str(x) for x in (meta.get("required_doc_ids") or [])]
    banned_phrases = [str(x) for x in (meta.get("answer_must_not_contain") or [])]

    if not forbidden and not required and not banned_phrases:
        return {
            "key": "rbac_dataset_docs",
            "score": 1.0,
            "comment": "skipped: no dataset RBAC expectations",
        }

    hits = _retrieve_hits(run_map)
    hit_ids = {str(h.get("doc_id") or "") for h in hits}
    answer = str(_run_outputs(run_map).get("answer") or "")

    problems: list[str] = []
    leaked = sorted(hit_ids & set(forbidden))
    if leaked:
        problems.append(f"forbidden_in_hits={leaked}")
    if required and not (hit_ids & set(required)):
        problems.append(f"missing_required={required} got={sorted(hit_ids)}")
    for phrase in banned_phrases:
        if phrase and phrase in answer:
            problems.append(f"answer_contains={phrase!r}")

    score = 1.0 if not problems else 0.0
    return {
        "key": "rbac_dataset_docs",
        "score": score,
        "comment": "; ".join(problems) if problems else f"ok hits={sorted(hit_ids)}",
    }


def pii_masked_not_in_answer(run: Any, example: Any) -> dict[str, Any]:
    """
    Deterministic: originals that were mask/redact'd in retrieve audit must not
    appear in the final answer. Optionally metadata.must_not_contain for extras.
    """
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    meta = _example_meta(example_map)
    answer = str(_run_outputs(run_map).get("answer") or "")
    hits = _retrieve_hits(run_map)

    originals: list[str] = []
    for hit in hits:
        for tr in hit.get("transformations") or []:
            if not isinstance(tr, dict):
                continue
            if tr.get("action") not in {"mask", "redact"}:
                continue
            original = str(tr.get("original") or "").strip()
            if original:
                originals.append(original)
    for extra in meta.get("must_not_contain") or []:
        text = str(extra).strip()
        if text:
            originals.append(text)

    # Dedupe while stable
    seen: set[str] = set()
    uniq: list[str] = []
    for o in originals:
        if o not in seen:
            seen.add(o)
            uniq.append(o)

    if not uniq:
        return {
            "key": "pii_masked_not_in_answer",
            "score": 1.0,
            "comment": "skipped: no masked originals / must_not_contain",
        }

    leaked = [o for o in uniq if o in answer]
    score = 1.0 if not leaked else 0.0
    return {
        "key": "pii_masked_not_in_answer",
        "score": score,
        "comment": f"checked={len(uniq)} leaked={leaked[:5]}",
    }


def pii_allowed_present_in_answer(run: Any, example: Any) -> dict[str, Any]:
    """
    Deterministic positive PII: metadata.must_contain strings should appear in
    the answer when the role is allowed to see them (e.g. HR email).
    """
    example_map = _as_mapping(example)
    run_map = _as_mapping(run)
    meta = _example_meta(example_map)
    required = [str(x).strip() for x in (meta.get("must_contain") or []) if str(x).strip()]
    if not required:
        return {
            "key": "pii_allowed_present_in_answer",
            "score": 1.0,
            "comment": "skipped: no must_contain",
        }
    answer = str(_run_outputs(run_map).get("answer") or "")
    missing = [s for s in required if s not in answer]
    score = 1.0 if not missing else 0.0
    return {
        "key": "pii_allowed_present_in_answer",
        "score": score,
        "comment": f"missing={missing}" if missing else "ok",
    }
