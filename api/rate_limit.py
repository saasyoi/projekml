import time

photo_bucket: dict = {}
login_bucket: dict = {}
register_bucket: dict = {}
chat_bucket: dict = {}


def check_rate_limit(bucket: dict, key: str, max_count: int, window_seconds: int) -> bool:
    now = time.time()
    history = [t for t in bucket.get(key, []) if now - t < window_seconds]
    bucket[key] = history
    return len(history) >= max_count


def record_event(bucket: dict, key: str) -> None:
    bucket.setdefault(key, []).append(time.time())
