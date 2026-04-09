-- Create segment for application-owned tables.
-- This schema stores product/UI data such as chat threads, messages, and events.
-- We keep it separate from LangGraph internal schemas on purpose.
create schema if not exists app;

-- Enable pgcrypto so we can use gen_random_uuid() for UUID primary keys.
create extension if not exists pgcrypto;

-- =========================================================
-- TABLE: app.chat_threads
-- =========================================================
-- This table represents one chat thread/conversation.
-- It is mainly used for sidebar listing, thread metadata,
-- archive state, and thread-level UI management.
create table if not exists app.chat_threads (
  -- Unique ID for the thread.
  -- This should also be reused as LangGraph's configurable.thread_id
  -- so the app thread and agent thread stay aligned.
  id uuid primary key default gen_random_uuid(),

  -- Owner of the thread.
  -- Useful for authorization and filtering threads per user.
  user_id uuid not null,

  -- Optional assistant/persona identifier.
  -- Helpful if one user can chat with multiple assistants.
  assistant_id text not null default 'default',

  -- Human-readable title shown in the UI sidebar.
  -- Can start with a default value and later be replaced by an AI-generated title.
  title text not null default 'New Chat',

  -- Indicates whether the title was generated automatically
  -- or is still the default/manual title.
  title_generated boolean not null default false,

  -- Soft archive flag for UI purposes.
  -- Archived threads are hidden from the main list but not deleted.
  archived boolean not null default false,

  -- Timestamp when the thread was first created.
  created_at timestamptz not null default now(),

  -- Timestamp when thread metadata was last updated.
  -- Example: title changed, archive status changed, etc.
  updated_at timestamptz not null default now(),

  -- Timestamp of the most recent message in the thread.
  -- Used to sort threads in the sidebar by latest activity.
  last_message_at timestamptz not null default now(),

  -- Flexible JSON field for extra thread-level metadata.
  -- Example: tags, UI state, custom settings, assistant version, etc.
  metadata jsonb not null default '{}'::jsonb
);

-- Index to efficiently list a user's threads ordered by recent activity.
create index if not exists idx_chat_threads_user_last_message
  on app.chat_threads (user_id, last_message_at desc);

-- =========================================================
-- TABLE: app.chat_messages
-- =========================================================
-- This table stores the full transcript shown in the product UI.
-- It is the source of truth for displayed history, not LangGraph checkpoints.
-- We store user messages, assistant replies, tool-related records, etc.
create table if not exists app.chat_messages (
  -- Unique ID for the message record.
  id uuid primary key default gen_random_uuid(),

  -- Parent thread reference.
  -- If a thread is deleted, all related message records are also removed.
  thread_id uuid not null references app.chat_threads(id) on delete cascade,

  -- Owner of the message/thread.
  -- Kept here for easier filtering and safer authorization patterns.
  user_id uuid not null,

  -- High-level actor role of the record.
  -- user      = end-user message
  -- assistant = final AI response
  -- tool      = tool-related record
  -- system    = internal/system message if needed
  role text not null check (role in ('user', 'assistant', 'tool', 'system')),

  -- More specific message type/category.
  -- Example values:
  -- message      = normal chat message
  -- tool_call    = tool invocation request
  -- tool_result  = tool output/result
  -- summary_note = optional UI-visible summary marker
  kind text not null default 'message',

  -- Logical turn identifier.
  -- One turn may include:
  -- - one user input
  -- - one or more tool calls/results
  -- - one final assistant response
  -- This makes it easy to group related records together.
  turn_id uuid not null,

  -- Name of the tool involved, if this row is tool-related.
  tool_name text,

  -- Provider/tool-specific call ID for tracing or debugging.
  tool_call_id text,

  -- Plain text content for easy rendering and simple querying.
  -- Good for most user/assistant text messages.
  content_text text,

  -- Structured JSON content for richer payloads.
  -- Example: tool arguments, citations, structured blocks, attachments, raw API payloads.
  content_json jsonb not null default '{}'::jsonb,

  -- Model name used to generate this message, if applicable.
  -- Example: gpt-4.1, gpt-5, etc.
  model_name text,

  -- Token usage metadata for observability/cost tracking.
  input_tokens integer,
  output_tokens integer,

  -- End-to-end latency for this message/tool record in milliseconds.
  latency_ms integer,

  -- Optional link to a LangGraph checkpoint/run identifier.
  -- Useful for debugging, but should not be used as the UI source of truth.
  checkpoint_id text,

  -- Creation timestamp of this message record.
  created_at timestamptz not null default now()
);

-- Index to load a thread's transcript in chronological order.
create index if not exists idx_chat_messages_thread_created
  on app.chat_messages (thread_id, created_at asc);

-- Index to quickly group/fetch all records belonging to the same conversational turn.
create index if not exists idx_chat_messages_turn
  on app.chat_messages (turn_id);

-- =========================================================
-- TABLE: app.chat_events
-- =========================================================
-- This table stores low-level runtime/audit events.
-- It is intentionally separate from chat_messages so the transcript stays clean.
-- Events can include streaming chunks, tool lifecycle events, node updates, errors, etc.
create table if not exists app.chat_events (
  -- Auto-incrementing event ID.
  -- Bigserial is fine here because events are append-only and can grow quickly.
  id bigserial primary key,

  -- Parent thread reference.
  -- Delete related events if the thread is deleted.
  thread_id uuid not null references app.chat_threads(id) on delete cascade,

  -- Link events to the logical user turn they belong to.
  turn_id uuid not null,

  -- Event category/type.
  -- Example values:
  -- token, stream_chunk, tool_start, tool_end, checkpoint, node_update, error
  event_type text not null,

  -- Optional LangGraph node name or internal execution step source.
  -- Useful for debugging graph behavior.
  node_name text,

  -- Raw event payload stored as JSON.
  -- Example: streamed token chunk, tool arguments/result, error details, checkpoint metadata.
  payload jsonb not null,

  -- Timestamp when the event was recorded.
  created_at timestamptz not null default now()
);

-- Index to efficiently retrieve events for one thread/turn in chronological order.
create index if not exists idx_chat_events_thread_turn_created
  on app.chat_events (thread_id, turn_id, created_at asc);
