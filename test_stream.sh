#!/bin/bash

# Ganti nilai-nilai di bawah sesuai kebutuhan
THREAD_ID="PASTE_THREAD_ID"
USER_ID="11111111-1111-1111-1111-111111111111"
MESSAGE="Jelaskan singkat apa itu LangGraph."

curl -N -X POST "http://127.0.0.1:8000/api/v1/chat/stream" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: stream-test-001" \
  -d "{
    \"thread_id\": \"$THREAD_ID\",
    \"user_id\": \"$USER_ID\",
    \"message\": \"$MESSAGE\"
  }"
