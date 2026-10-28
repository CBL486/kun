# ADR: Reusable Scoped Memory Core

Status: implemented in SQLite; PostgreSQL parity pending  
Date: 2026-10-26

## Decision

Create a standalone `memory_core` package shared by the QQ companion and AI
School. The package owns data models, storage interfaces, recall scoring,
lifecycle transitions, and contract tests. It does not import QQ plugin or
school domain models.

QQ and School are separate tenants. They do not share memory namespaces and do
not automatically recall one another's records.

## Scope

A canonical scope contains:

```text
tenant_id
world_id
user_id
character_id
surface
conversation_id
```

`tenant_id`, `user_id`, `character_id`, and `surface` are mandatory and must be
non-empty after normalization. `world_id` is optional for surfaces without a
world. `conversation_id` is optional only for operations defined as character-
or world-wide.

Every query is bounded by the complete provided scope. The store must not infer
missing dimensions, fall back to a global query, or permit wildcard matching.
An explicit character-wide query is a separate method mode and cannot be
activated accidentally.

## Identity and idempotency

- `id` is a UUID.
- A caller may provide `dedupe_key`; `(scope, dedupe_key)` is unique.
- Event hooks provide an idempotent `operation_id` or `source_event_id`.
- Repeating the same write or reinforcement returns the original outcome
  without adding another row or another strength bonus.
- Concurrent writes in one scope must serialize or retry without data loss.
- Reusing a `dedupe_key` with different semantic fields is a `ConflictError`.
  An omitted retry timestamp does not by itself conflict; an explicitly
  different timestamp does.

## Memory record

All scalar weights are in `[0, 1]`. Emotional weight is stored as intensity;
its sign, if needed by a product surface, belongs in metadata.

| Field | Required | Semantics |
| --- | --- | --- |
| `id` | yes | UUID |
| `scope` | yes | Canonical six-dimension scope |
| `content` | yes | Non-empty normalized text |
| `kind` | yes | `fact`, `preference`, `relationship`, `plan`, `emotion`, `event`, `reflection`, or `summary` |
| `source` | yes | `chat`, `school_event`, `daily_share`, `diary`, `autonomy`, or `system` |
| `importance` | yes | Stable semantic importance |
| `emotional_weight` | yes | Emotional intensity |
| `confidence` | yes | Confidence in the extracted memory |
| `strength` | yes | Current retrievability |
| `scene_tags` | yes | Deduplicated, normalized tags |
| `created_at` | yes | UTC-aware timestamp |
| `last_accessed_at` | no | UTC-aware timestamp |
| `last_strength_update` | yes | Decay baseline timestamp |
| `access_count` | yes | Non-negative integer |
| `restated_count` | yes | Non-negative integer |
| `locked` | yes | Locked records do not decay |
| `state` | yes | `active`, `fuzzy`, or `archived` |
| `source_event_id` | no | Upstream event identity |
| `dedupe_key` | no | Scoped write idempotency key |
| `metadata` | yes | JSON-compatible object |

The task-book field list remains the minimum. `last_strength_update`,
`dedupe_key`, and `operation_id` are required additions for deterministic decay
and idempotency.

## Lifecycle

- `strength >= 0.3`: `active`
- `0.1 <= strength < 0.3`: `fuzzy`
- `strength < 0.1`: `archived`
- Locked records remain `active` and do not decay.
- Unlocking does not immediately decay a record; it resumes the normal decay
  process from the unlock moment.
- Archived records are excluded from default recall.
- Fuzzy records may be recalled with their state and lower retrieval priority.
- There is no automatic deletion. Archive is reversible and data-retaining.
- An explicitly archived record remains archived through later decay passes.
  A qualifying reinforcement may reactivate it; this is the current
  "restatement restores a memory" path.

Decay uses elapsed time since `last_strength_update`; it must not repeatedly
apply the full half-life after each scheduler run. A configurable half-life and
minimum floor are required. The exact production values remain provisional.

## Reinforcement

Supported reasons:

```text
share
restatement
scene_trigger
flow
manual
```

Each reason has a configured base delta. Reinforcement updates strength,
`last_strength_update`, reason-specific metadata, and the relevant count. It is
idempotent per operation. A reinforcement cannot exceed `1.0`.

## Recall

The default score is:

```text
score =
    relevance * 0.40
  + strength * 0.20
  + importance * 0.15
  + emotional_weight * 0.10
  + recency * 0.10
  + access_bonus * 0.05
```

All weights are configuration. Relevance is computed from normalized query
terms, scene-tag overlap, and explicit event association. Result ordering breaks
ties by score, then importance, strength, recency, and ID.

Every recall result includes:

```text
memory
score
relevance
strength
importance
emotional_weight
recency
access_bonus
state
```

`budget` limits selected records and optional approximate token count. A recall
is a read operation; it may update access counters and activation timestamps,
but it must not silently strengthen semantic importance.

`source_event_id` values are identifiers, not tags. They preserve case and are
matched exactly. `scene_tags` are normalized to case-folded tags.

## Error semantics

- `ScopeError`: malformed or incomplete scope.
- `ValidationError`: invalid field value or transition.
- `NotFoundError`: ID does not exist inside the supplied scope.
- `ConflictError`: conflicting idempotency key or concurrent update.
- `BackendUnavailable`: operational backend failure.

No error response may contain credentials, raw user content, or SQL parameters.

## Backend mapping

SQLite and PostgreSQL implement the same protocol.

- SQLite is for local tests and single-process development.
- PostgreSQL is the production and staging backend.
- Both store `scene_tags` as normalized JSON arrays and `metadata` as JSON.
- Both enforce scope fields, bounded weights, and the scoped dedupe key.
- JSONB indexing is PostgreSQL-specific and invisible to callers.
- PostgreSQL time values are UTC `timestamptz`; SQLite stores ISO-8601 UTC text
  and converts at the adapter boundary.

## Migration

Migration is copy-first and reversible:

1. Create and verify a backup outside the migration process.
2. Import old `messages` and `summaries` into a staging namespace.
3. Reconcile counts and selected synthetic checksums.
4. Run QQ smoke tests against the migrated SQLite copy.
5. Switch only after both counts and behavior checks pass.
6. Retain the pre-migration database until the rollback window closes.

Detailed field mapping is in `docs/migrations/qq-memory-mapping.md`.

## Public model names

The canonical Python names are `Scope`, `MemoryCoreConfig`, `MemoryDraft`, and
`RecallQuery`. `MemoryScope` and `MemoryConfig` remain compatibility aliases for
early adapter drafts; new code should use the canonical names.

## Consequences

The shared engine will need a small amount of storage glue in each product,
but neither product may reach directly into the other's tables. The strict
scope contract trades some convenience for testable isolation and explainable
recall.

