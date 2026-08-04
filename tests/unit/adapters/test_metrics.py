from urlshortener.adapters.metrics import RequestCounters, get_counters, reset_counters


def test_record_increments_total_requests():
    counters = RequestCounters()

    counters.record(status_code=200, duration_ms=5.0, is_redirect=False)
    counters.record(status_code=201, duration_ms=8.0, is_redirect=False)

    assert counters.total_requests == 2


def test_record_buckets_status_codes_by_class():
    counters = RequestCounters()

    counters.record(status_code=201, duration_ms=1.0, is_redirect=False)
    counters.record(status_code=302, duration_ms=1.0, is_redirect=True)
    counters.record(status_code=404, duration_ms=1.0, is_redirect=False)
    counters.record(status_code=500, duration_ms=1.0, is_redirect=False)

    assert counters.status_class_counts == {"2xx": 1, "3xx": 1, "4xx": 1, "5xx": 1}


def test_record_tracks_redirect_latency_only_for_redirects():
    counters = RequestCounters()

    counters.record(status_code=201, duration_ms=100.0, is_redirect=False)
    counters.record(status_code=302, duration_ms=5.0, is_redirect=True)
    counters.record(status_code=302, duration_ms=15.0, is_redirect=True)

    assert counters.redirect_count == 2
    assert counters.redirect_latency_min_ms == 5.0
    assert counters.redirect_latency_max_ms == 15.0
    assert counters.redirect_latency_sum_ms == 20.0


def test_summary_computes_error_rate():
    counters = RequestCounters()
    for _ in range(3):
        counters.record(status_code=200, duration_ms=1.0, is_redirect=False)
    counters.record(status_code=404, duration_ms=1.0, is_redirect=False)

    summary = counters.summary()

    assert summary["total_requests"] == 4
    assert summary["error_rate"] == 0.25


def test_summary_with_zero_requests_does_not_divide_by_zero():
    counters = RequestCounters()

    summary = counters.summary()

    assert summary["total_requests"] == 0
    assert summary["error_rate"] == 0.0
    assert summary["redirect_avg_latency_ms"] is None


def test_summary_computes_redirect_average_latency():
    counters = RequestCounters()
    counters.record(status_code=302, duration_ms=10.0, is_redirect=True)
    counters.record(status_code=302, duration_ms=20.0, is_redirect=True)

    summary = counters.summary()

    assert summary["redirect_avg_latency_ms"] == 15.0
    assert summary["redirect_min_latency_ms"] == 10.0
    assert summary["redirect_max_latency_ms"] == 20.0


def test_summary_with_no_redirects_has_none_latency_fields():
    counters = RequestCounters()
    counters.record(status_code=201, duration_ms=1.0, is_redirect=False)

    summary = counters.summary()

    assert summary["redirect_count"] == 0
    assert summary["redirect_avg_latency_ms"] is None
    assert summary["redirect_min_latency_ms"] is None
    assert summary["redirect_max_latency_ms"] is None


def test_get_counters_returns_the_same_process_wide_instance():
    reset_counters()
    first = get_counters()
    first.record(status_code=200, duration_ms=1.0, is_redirect=False)

    second = get_counters()

    assert second is first
    assert second.total_requests == 1


def test_reset_counters_replaces_the_singleton():
    get_counters().record(status_code=200, duration_ms=1.0, is_redirect=False)

    reset_counters()

    assert get_counters().total_requests == 0
