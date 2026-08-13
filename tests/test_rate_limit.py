from api.rate_limit import check_rate_limit, record_event


def test_allows_up_to_max_count():
    bucket = {}
    for _ in range(5):
        assert check_rate_limit(bucket, "user1", max_count=5, window_seconds=60) is False
        record_event(bucket, "user1")
    assert check_rate_limit(bucket, "user1", max_count=5, window_seconds=60) is True


def test_keys_are_independent():
    bucket = {}
    for _ in range(5):
        record_event(bucket, "user1")
    assert check_rate_limit(bucket, "user1", max_count=5, window_seconds=60) is True
    assert check_rate_limit(bucket, "user2", max_count=5, window_seconds=60) is False


def test_events_outside_window_are_ignored():
    bucket = {"user1": [0.0, 0.0, 0.0, 0.0, 0.0]}  # far in the past
    assert check_rate_limit(bucket, "user1", max_count=5, window_seconds=60) is False
