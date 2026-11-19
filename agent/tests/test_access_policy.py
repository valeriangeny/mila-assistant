"""Unit tests for role → document access policy (no Qdrant / network)."""

from __future__ import annotations

import pytest

from mila_agent.access_policy import (
    AUDIENCES,
    ROLE_ACCESS,
    SENSITIVITIES,
    access_for_role,
    document_allowed,
    known_roles,
    normalize_role,
    qdrant_filter_for_role,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("employee", "employee"),
        ("HR", "hr"),
        (" Engineering ", "engineering"),
        ("", "employee"),
        (None, "employee"),
        ("admin", "employee"),  # unknown → least privilege
    ],
)
def test_normalize_role(raw: str | None, expected: str) -> None:
    assert normalize_role(raw) == expected


def test_known_roles_cover_sample_users() -> None:
    assert set(known_roles()) == {"employee", "hr", "engineering", "security"}


def test_policy_vocab_is_subset_of_dictionary() -> None:
    for scope in ROLE_ACCESS.values():
        assert scope.audiences <= AUDIENCES
        assert scope.sensitivities <= SENSITIVITIES


@pytest.mark.parametrize(
    ("role", "audience", "sensitivity", "allowed"),
    [
        # employee: company-wide public/internal only
        ("employee", "company-wide", "public", True),
        ("employee", "company-wide", "internal", True),
        ("employee", "company-wide", "confidential", False),
        ("employee", "company-wide", "restricted", False),
        ("employee", "people-ops", "internal", False),
        ("employee", "engineering", "internal", False),
        ("employee", "function-leads", "internal", False),
        # hr: people-ops + restricted OK; engineering audience not
        ("hr", "people-ops", "restricted", True),
        ("hr", "people-ops-and-security", "confidential", True),
        ("hr", "function-leads", "restricted", True),
        ("hr", "company-wide", "internal", True),
        ("hr", "engineering", "internal", False),
        ("hr", "security", "restricted", False),
        # engineering: engineering audiences; no restricted
        ("engineering", "engineering", "confidential", True),
        ("engineering", "engineering-and-security", "internal", True),
        ("engineering", "function-leads", "confidential", True),
        ("engineering", "engineering", "restricted", False),
        ("engineering", "people-ops", "internal", False),
        ("engineering", "security", "confidential", False),
        # security: security + shared; restricted OK
        ("security", "security", "restricted", True),
        ("security", "engineering-and-security", "confidential", True),
        ("security", "people-ops-and-security", "restricted", True),
        ("security", "function-leads", "restricted", True),
        ("security", "people-ops", "internal", False),
        ("security", "engineering", "internal", False),
    ],
)
def test_document_allowed(
    role: str,
    audience: str,
    sensitivity: str,
    allowed: bool,
) -> None:
    assert (
        document_allowed(
            role,
            intended_audience=audience,
            sensitivity=sensitivity,
        )
        is allowed
    )


def test_empty_metadata_denied() -> None:
    assert document_allowed("hr", intended_audience="", sensitivity="internal") is False
    assert document_allowed("hr", intended_audience="people-ops", sensitivity="") is False


def test_access_for_role_matches_table() -> None:
    scope = access_for_role("security")
    assert scope.role == "security"
    assert "security" in scope.audiences
    assert "restricted" in scope.sensitivities


def test_qdrant_filter_shape() -> None:
    filt = qdrant_filter_for_role("employee")
    assert filt.must is not None
    assert len(filt.must) == 2
    keys = {cond.key for cond in filt.must}
    assert keys == {"intended_audience", "sensitivity"}
    by_key = {cond.key: set(cond.match.any) for cond in filt.must}
    assert by_key["intended_audience"] == set(ROLE_ACCESS["employee"].audiences)
    assert by_key["sensitivity"] == set(ROLE_ACCESS["employee"].sensitivities)


# Corpus-flavored fixtures (metadata only — not full docs).
@pytest.mark.parametrize(
    ("role", "doc_id", "audience", "sensitivity", "allowed"),
    [
        # Welcome / company-wide: all roles
        ("employee", "DOC-0022", "company-wide", "public", True),
        ("hr", "DOC-0022", "company-wide", "public", True),
        # Maya accommodation (restricted, people-ops): hr only among samples
        ("employee", "DOC-0041", "people-ops", "restricted", False),
        ("hr", "DOC-0041", "people-ops", "restricted", True),
        ("engineering", "DOC-0041", "people-ops", "restricted", False),
        ("security", "DOC-0041", "people-ops", "restricted", False),
        # Engineering runbook internal
        ("employee", "DOC-0049", "company-wide", "internal", True),
        ("engineering", "runbook-eng", "engineering", "internal", True),
        ("employee", "runbook-eng", "engineering", "internal", False),
    ],
)
def test_representative_docs(
    role: str,
    doc_id: str,
    audience: str,
    sensitivity: str,
    allowed: bool,
) -> None:
    assert (
        document_allowed(
            role,
            intended_audience=audience,
            sensitivity=sensitivity,
        )
        is allowed
    ), f"{role} vs {doc_id}"
