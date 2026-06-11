create table if not exists app.chat_requests (
  id uuid primary key default gen_random_uuid(),

  thread_id uuid not null references app.chat_threads(id) on delete cascade,
  user_id uuid not null,

  idempotency_key text not null,
  request_hash text not null,

  status text not null check (status in ('started', 'succeeded', 'failed')),

  turn_id uuid,
  response_json jsonb,
  error_text text,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  unique (user_id, thread_id, idempotency_key)
);

create index if not exists idx_chat_requests_thread_created
  on app.chat_requests (thread_id, created_at desc);