DROP TABLE IF EXISTS npc_memory_slots;
DROP TABLE IF EXISTS memory_mutations;
DROP TABLE IF EXISTS memories;
DROP TABLE IF EXISTS memory_projection_outbox;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS actions;
DROP TABLE IF EXISTS world_versions;
DROP TABLE IF EXISTS world_heads;
DELETE FROM schema_versions WHERE version = 1;
