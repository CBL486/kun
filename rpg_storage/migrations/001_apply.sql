CREATE TABLE IF NOT EXISTS world_heads (
    world_id TEXT PRIMARY KEY,
    state_version INTEGER NOT NULL CHECK (state_version >= 0),
    logical_time TEXT NOT NULL,
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS world_versions (
    world_id TEXT NOT NULL,
    state_version INTEGER NOT NULL,
    logical_time TEXT NOT NULL,
    state_json TEXT NOT NULL,
    event_id TEXT,
    created_at TEXT NOT NULL,
    PRIMARY KEY (world_id, state_version)
);

CREATE TABLE IF NOT EXISTS actions (
    operation_id TEXT PRIMARY KEY,
    action_id TEXT NOT NULL UNIQUE,
    world_id TEXT NOT NULL,
    character_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    tick_id TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    status TEXT NOT NULL,
    event_id TEXT,
    payload_json TEXT NOT NULL,
    committed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    world_id TEXT NOT NULL,
    world_date TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    slot_key TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    visibility TEXT NOT NULL,
    tick_id TEXT NOT NULL,
    action_id TEXT NOT NULL UNIQUE,
    event_json TEXT NOT NULL,
    committed_at TEXT NOT NULL,
    UNIQUE (world_id, world_date, sequence)
);

CREATE TABLE IF NOT EXISTS memory_projection_outbox (
    projection_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL REFERENCES events(event_id),
    candidate_index INTEGER NOT NULL,
    character_id TEXT NOT NULL,
    dedupe_key TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'projected', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (event_id, candidate_index)
);

CREATE TABLE IF NOT EXISTS memories (
    memory_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    world_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    character_id TEXT NOT NULL,
    surface TEXT NOT NULL,
    conversation_id TEXT,
    conversation_key TEXT NOT NULL,
    scope_hash TEXT NOT NULL,
    kind TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    importance REAL NOT NULL CHECK (importance >= 0 AND importance <= 1),
    emotional_weight REAL NOT NULL CHECK (emotional_weight >= 0 AND emotional_weight <= 1),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    strength REAL NOT NULL CHECK (strength >= 0 AND strength <= 1),
    scene_tags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed_at TEXT,
    last_strength_update TEXT NOT NULL,
    access_count INTEGER NOT NULL DEFAULT 0,
    restated_count INTEGER NOT NULL DEFAULT 0,
    locked INTEGER NOT NULL DEFAULT 0 CHECK (locked IN (0, 1)),
    state TEXT NOT NULL CHECK (state IN ('active', 'fuzzy', 'archived')),
    source_event_id TEXT NOT NULL REFERENCES events(event_id),
    dedupe_key TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    UNIQUE (scope_hash, dedupe_key)
);

CREATE TABLE IF NOT EXISTS memory_mutations (
    operation_id TEXT PRIMARY KEY,
    memory_id TEXT NOT NULL REFERENCES memories(memory_id),
    source_event_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    amount REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS npc_memory_slots (
    npc_id TEXT NOT NULL,
    slot_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    content_key TEXT NOT NULL,
    source_event_id TEXT,
    important INTEGER NOT NULL CHECK (important IN (0, 1)),
    expires_on TEXT,
    last_used_at TEXT,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (npc_id, slot_id)
);

CREATE INDEX IF NOT EXISTS idx_memories_scope_state
    ON memories(scope_hash, state);
CREATE INDEX IF NOT EXISTS idx_memories_source_event
    ON memories(source_event_id);
CREATE INDEX IF NOT EXISTS idx_events_world_time
    ON events(world_id, world_date, sequence);
CREATE INDEX IF NOT EXISTS idx_outbox_status
    ON memory_projection_outbox(status);
