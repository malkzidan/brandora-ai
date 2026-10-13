from app.pipeline.throttle import SlidingWindowThrottle, throttle_key


class Clock:
    def __init__(self): self.t = 1000.0
    def __call__(self): return self.t


def test_allows_up_to_the_limit_then_blocks():
    clock = Clock(); th = SlidingWindowThrottle(3, 60, clock)
    assert [th.hit("a") for _ in range(3)] == [None, None, None]
    wait = th.hit("a")
    assert wait is not None and 0 < wait <= 60


def test_window_slides():
    clock = Clock(); th = SlidingWindowThrottle(2, 60, clock)
    th.hit("a"); clock.t += 30; th.hit("a")
    assert th.hit("a") is not None
    clock.t += 31                       # first hit left the window
    assert th.hit("a") is None


def test_blocked_hits_do_not_extend_the_block():
    clock = Clock(); th = SlidingWindowThrottle(1, 10, clock)
    th.hit("a")
    for _ in range(50):
        assert th.hit("a") is not None
    clock.t += 10
    assert th.hit("a") is None


def test_keys_are_independent():
    th = SlidingWindowThrottle(1, 60, Clock())
    assert th.hit("a") is None and th.hit("b") is None and th.hit("a") is not None


def test_retry_after_shrinks_over_time():
    clock = Clock(); th = SlidingWindowThrottle(1, 60, clock)
    th.hit("a"); first = th.hit("a"); clock.t += 20; second = th.hit("a")
    assert second < first


def test_prune_removes_expired_keys():
    clock = Clock(); th = SlidingWindowThrottle(5, 10, clock)
    for i in range(1001):
        th.hit(f"k{i}")
    clock.t += 11
    th.hit("fresh")
    assert len(th._hits) < 50


def test_throttle_key():
    assert throttle_key({"id": "b1"}, {"id": "c1"}) == "b1:c1"
    assert throttle_key({"id": "b1"}, {"phone": "0101"}) == "b1:0101"
    assert throttle_key({"id": "b1"}, {}) is None
    assert throttle_key({}, {"id": "c1"}) == ":c1"
