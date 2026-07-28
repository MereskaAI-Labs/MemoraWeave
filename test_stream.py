import requests
import json

# Konfigurasi parameter
URL = "http://127.0.0.1:8000/api/v1/chat/stream"
THREAD_ID = "fb0640d3-cc7b-4105-9204-05f171f44219"
USER_ID = "11111111-1111-1111-1111-111111111111"

# 9A Test
MESSAGE = "Jelaskan singkat apa itu LangGraph."
IDEM_KEY = "stream-test-001"

# 9B Test
MESSAGE = "Sekarang project backend saya sedang di tahap apa? Gunakan tool kalau relevan."
IDEM_KEY = "stream-tool-test-001"

headers = {
    "Content-Type": "application/json",
    "Idempotency-Key": IDEM_KEY
}

data = {
    "thread_id": THREAD_ID,
    "user_id": USER_ID,
    "message": MESSAGE
}

def main():
    print(f"Sending request to {URL}...")
    try:
        # stream=True sangat penting untuk menerima response streaming dari server
        with requests.post(URL, headers=headers, json=data, stream=True) as response:
            response.raise_for_status()
            
            print("Response stream:")
            # Iterasi setiap chunk yang diterima
            for chunk in response.iter_content(chunk_size=None):
                if chunk:
                    # Cetak langsung ke terminal tanpa newline tambahan
                    print(chunk.decode('utf-8'), end='', flush=True)
            print("\n\n[Stream selesai]")
            
    except requests.exceptions.RequestException as e:
        print(f"\n[Error]: {e}")

if __name__ == "__main__":
    main()
