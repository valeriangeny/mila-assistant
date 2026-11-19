"""Role → document access policy (self-contained, table-driven).

This module is the single place to edit who may see which documents.

## Model

A **verified** role (from auth / `users.json`, not invented by the LLM) maps to
allow-lists:

- ``intended_audience`` — primary gate (who the doc was written for)
- ``sensitivity`` — ceiling (how sensitive a doc may be)

``department`` is **not** part of the default gate. Owning team is a weak signal
compared to audience; add it later only if you need tighter ownership rules.

A document is allowed iff::

    doc.intended_audience ∈ role.audiences
    AND doc.sensitivity ∈ role.sensitivities

Unknown *role strings* fall back to ``employee``. Incognito browsing uses the
explicit ``public`` role (stricter than employee: company-wide + ``public``
sensitivity only). Unauthenticated callers must not search at all — that gate
lives in ``retrieve_knowledge`` via ``auth_mode``.

## How to modify

1. Edit ``ROLE_ACCESS`` below (add/remove audience or sensitivity strings).
2. Keep values aligned with ``instructions/data_dictionary.md``.
3. Run ``uv run pytest tests/test_access_policy.py`` — no Qdrant required.

## Trust boundary

Callers must pass a **verified** role (or opt into ``public`` via incognito).
``retrieve_knowledge`` reads ``auth_mode`` + role from LangGraph
``AgentContext`` / auth (CopilotKit mock OIDC), not from the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, FrozenSet, Iterable, Mapping

# --- Vocabulary (data dictionary) -------------------------------------------------

Role = str

SENSITIVITIES: FrozenSet[str] = frozenset(
    {"public", "internal", "confidential", "restricted"}
)

AUDIENCES: FrozenSet[str] = frozenset(
    {
        "company-wide",
        "people-ops",
        "engineering",
        "security",
        "engineering-and-security",
        "people-ops-and-security",
        "function-leads",
    }
)

# Baseline staff: company-wide material that is not tightly held.
_EMPLOYEE_AUDIENCES = frozenset({"company-wide"})
_EMPLOYEE_SENSITIVITIES = frozenset({"public", "internal"})

# Function leads + shared audiences used by privileged roles.
_FUNCTION_LEAD_AUDIENCES = frozenset({"function-leads"})


@dataclass(frozen=True, slots=True)
class AccessScope:
    """Allow-lists for one role. Edit via ``ROLE_ACCESS``, not ad-hoc code."""

    role: str
    audiences: FrozenSet[str]
    sensitivities: FrozenSet[str]

    def allows(
        self,
        *,
        intended_audience: str,
        sensitivity: str,
    ) -> bool:
        """Return True if a document with these metadata fields is visible."""
        return (
            intended_audience in self.audiences
            and sensitivity in self.sensitivities
        )


# --- Policy table (edit here) -----------------------------------------------------
#
# Design notes (defendable defaults for the take-home):
# - public: incognito / guest — company-wide + sensitivity public only (stricter
#   than employee; no internal).
# - employee: company-wide public/internal only.
# - hr: people-ops (+ shared with security) and function-leads; all sensitivities
#   (HR owns restricted profiles / leave / comp).
# - engineering: engineering (+ shared with security) and function-leads;
#   up through confidential (restricted security/HR stays out).
# - security: security (+ both shared) and function-leads; all sensitivities.
#
# company-wide is included for staff roles so general policies remain visible.

ROLE_ACCESS: Mapping[str, AccessScope] = {
    "public": AccessScope(
        role="public",
        audiences=frozenset({"company-wide"}),
        sensitivities=frozenset({"public"}),
    ),
    "employee": AccessScope(
        role="employee",
        audiences=_EMPLOYEE_AUDIENCES,
        sensitivities=_EMPLOYEE_SENSITIVITIES,
    ),
    "hr": AccessScope(
        role="hr",
        audiences=frozenset(
            {
                "company-wide",
                "people-ops",
                "people-ops-and-security",
            }
            | _FUNCTION_LEAD_AUDIENCES
        ),
        sensitivities=frozenset(SENSITIVITIES),
    ),
    "engineering": AccessScope(
        role="engineering",
        audiences=frozenset(
            {
                "company-wide",
                "engineering",
                "engineering-and-security",
            }
            | _FUNCTION_LEAD_AUDIENCES
        ),
        sensitivities=frozenset({"public", "internal", "confidential"}),
    ),
    "security": AccessScope(
        role="security",
        audiences=frozenset(
            {
                "company-wide",
                "security",
                "engineering-and-security",
                "people-ops-and-security",
            }
            | _FUNCTION_LEAD_AUDIENCES
        ),
        sensitivities=frozenset(SENSITIVITIES),
    ),
}

DEFAULT_ROLE = "employee"


def normalize_role(role: str | None) -> str:
    """Map empty/unknown roles to ``DEFAULT_ROLE`` (least privilege)."""
    if not role:
        return DEFAULT_ROLE
    key = role.strip().lower()
    return key if key in ROLE_ACCESS else DEFAULT_ROLE


def access_for_role(role: str | None) -> AccessScope:
    """Resolve the access scope for a verified role string."""
    return ROLE_ACCESS[normalize_role(role)]


def document_allowed(
    role: str | None,
    *,
    intended_audience: str,
    sensitivity: str,
) -> bool:
    """Pure predicate: may ``role`` see a doc with this metadata?

    Prefer this in unit tests. Empty/unknown audience or sensitivity → deny.
    """
    if not intended_audience or not sensitivity:
        return False
    return access_for_role(role).allows(
        intended_audience=intended_audience,
        sensitivity=sensitivity,
    )


def qdrant_filter_for_role(role: str | None) -> Any:
    """Build a Qdrant ``Filter`` for filtered vector search.

    Returns a ``qdrant_client.http.models.Filter`` with ``must`` conditions on
    ``intended_audience`` and ``sensitivity`` (keyword payload indexes).
    """
    from qdrant_client.http import models as qm

    scope = access_for_role(role)
    return qm.Filter(
        must=[
            qm.FieldCondition(
                key="intended_audience",
                match=qm.MatchAny(any=sorted(scope.audiences)),
            ),
            qm.FieldCondition(
                key="sensitivity",
                match=qm.MatchAny(any=sorted(scope.sensitivities)),
            ),
        ]
    )


def known_roles() -> Iterable[str]:
    """Roles present in the policy table (stable order)."""
    return tuple(ROLE_ACCESS.keys())
