-- =========================================================
-- FILE: 001_init_app_chat.sql
-- PURPOSE:
--   Initialize application-owned database structures for:
--   - chat thread list / sidebar
--   - full message transcript
--   - runtime/audit events
--
-- IMPORTANT:
--   These tables belong to the PRODUCT / APPLICATION layer,
--   not to LangGraph internal persistence.
--
--   LangGraph internal checkpoint/store tables should be created
--   later by LangGraph itself via its official setup() methods.
-- =========================================================


-- =========================================================
-- SCHEMAS
-- =========================================================

-- Application-owned schema.
-- This schema stores product/UI tables such as:
-- - chat_threads
-- - chat_messages
-- - chat_events
create schema if not exists app;

-- Reserved schema for LangGraph checkpoint internals.
-- We create the schema now for clean separation,
-- but LangGraph should create its own internal tables later.
create schema if not exists langgraph_ckpt;

-- Reserved schema for LangGraph long-term memory store internals.
-- Same idea: we reserve the schema, but do not manually define
-- LangGraph's internal tables here.
create schema if not exists langgraph_store;


-- =========================================================
-- EXTENSIONS
-- =========================================================

-- Enable pgcrypto so we can use gen_random_uuid()
-- for UUID primary keys.
create extension if not exists pgcrypto;


-- =========================================================
-- TABLE: app.chat_threads
-- =========================================================
-- This table represents a single chat/conversation thread.
-- It is mainly used for:
-- - sidebar listing
-- - thread title
-- - archive state
-- - sorting by latest activity
create table if not exists app.chat_threads (
  -- Unique thread ID.
  -- This should later be reused as LangGraph's thread_id
  -- so UI thread identity and agent thread identity stay aligned.
  id uuid primary key default gen_random_uuid(),

  -- Owner of the thread.
  -- Used for filtering, authorization, and multi-user support.
  user_id uuid not null,

  -- Assistant/persona identifier.
  -- Useful if one system supports multiple assistants.
  assistant_id text not null default 'default',

  -- Human-readable title shown in the sidebar.
  title text not null default 'New Chat',

  -- Indicates whether the title was generated automatically
  -- or is still a default/manual title.
  title_generated boolean not null default false,

  -- Soft archive flag.
  -- Archived threads can be hidden from the main UI
  -- without actually deleting them.
  archived boolean not null default false,

  -- Creation timestamp.
  created_at timestamptz not null default now(),

  -- Timestamp for thread metadata updates.
  -- Example: title changes, archive changes, etc.
  updated_at timestamptz not null default now(),

  -- Timestamp of the most recent activity/message in this thread.
  -- Useful for sorting sidebar items by recency.
  last_message_at timestamptz not null default now(),

  -- Flexible metadata container for future needs.
  -- Example: tags, settings, UI-specific flags, custom properties.
  metadata jsonb not null default '{}'::jsonb
);

-- Index for efficiently listing a user's threads
-- ordered by latest activity.
create index if not exists idx_chat_threads_user_last_message
  on app.chat_threads (user_id, last_message_at desc);


-- =========================================================
-- TABLE: app.chat_messages
-- =========================================================
-- This table stores the full chat transcript shown in the UI.
-- It is the PRODUCT source of truth for conversation history.
--
-- IMPORTANT:
-- Do not use LangGraph checkpoint tables as the UI transcript source.
-- Keep transcript history in this application table instead.
create table if not exists app.chat_messages (
  -- Unique ID for this message row.
  id uuid primary key default gen_random_uuid(),

  -- Parent thread reference.
  -- If the thread is deleted, its messages are deleted too.
  thread_id uuid not null references app.chat_threads(id) on delete cascade,

  -- Owner of the thread/message.
  -- Kept here for easier filtering and authorization checks.
  user_id uuid not null,

  -- High-level role of the message record.
  -- Allowed values:
  -- - user
  -- - assistant
  -- - tool
  -- - system
  role text not null check (role in ('user', 'assistant', 'tool', 'system')),

  -- More specific category of the message row.
  -- Examples:
  -- - message
  -- - tool_call
  -- - tool_result
  -- - summary_note
  kind text not null default 'message',

  -- Logical turn ID.
  -- A single turn may include:
  -- - one user message
  -- - one or more tool calls/results
  -- - one final assistant response
  --
  -- This helps group related records together.
  turn_id uuid not null,

  -- Tool name, if this row is related to a tool interaction.
  tool_name text,

  -- Tool/provider call identifier for tracing/debugging.
  tool_call_id text,

  -- Plain text version of the content.
  -- Good for normal rendering and simple search/display.
  content_text text,

  -- Structured JSON version of the content.
  -- Useful for richer payloads such as:
  -- - tool arguments
  -- - tool results
  -- - citations
  -- - structured blocks
  -- - attachments
  content_json jsonb not null default '{}'::jsonb,

  -- Model/provider model name used to generate this row.
  model_name text,

  -- Token usage metadata.
  -- Useful for cost tracking and observability.
  input_tokens integer,
  output_tokens integer,

  -- Latency in milliseconds for this message/tool operation.
  latency_ms integer,

  -- Optional internal reference to a checkpoint/run ID.
  -- Useful for debugging, but not for UI source-of-truth purposes.
  checkpoint_id text,

  -- Row creation timestamp.
  created_at timestamptz not null default now()
);

-- Index for loading one thread's transcript in chronological order.
create index if not exists idx_chat_messages_thread_created
  on app.chat_messages (thread_id, created_at asc);

-- Index for loading/grouping all records that belong to one turn.
create index if not exists idx_chat_messages_turn
  on app.chat_messages (turn_id);


-- =========================================================
-- TABLE: app.chat_events
-- =========================================================
-- This table stores low-level runtime or audit events.
-- It is intentionally separated from chat_messages so that:
-- - transcript stays clean
-- - debugging data stays available
--
-- Example events:
-- - stream_chunk
-- - tool_start
-- - tool_end
-- - checkpoint
-- - node_update
-- - error
create table if not exists app.chat_events (
  -- Auto-incrementing event ID.
  id bigserial primary key,

  -- Parent thread reference.
  thread_id uuid not null references app.chat_threads(id) on delete cascade,

  -- Logical turn reference.
  -- Connects runtime events to one conversational turn.
  turn_id uuid not null,

  -- Type/category of the event.
  event_type text not null,

  -- Optional graph node name or execution step name.
  -- Useful for debugging LangGraph flow later.
  node_name text,

  -- JSON payload containing raw event details.
  -- Example:
  -- - streamed token chunk
  -- - tool args / outputs
  -- - error details
  -- - checkpoint metadata
  payload jsonb not null,

  -- Timestamp when the event was recorded.
  created_at timestamptz not null default now()
);

-- Index for loading events by thread and turn in chronological order.
create index if not exists idx_chat_events_thread_turn_created
  on app.chat_events (thread_id, turn_id, created_at asc);
