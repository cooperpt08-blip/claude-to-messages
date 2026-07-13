from prediction_market_bot import edge
from prediction_market_bot.simulate import DEFAULT_SOURCES, generate_synthetic_history


def test_generate_synthetic_history_shape():
    history = generate_synthetic_history(n_steps=20, seed=1)
    assert len(history) == 20

    for timestamp, quotes in history:
        assert len(quotes) == len(DEFAULT_SOURCES)
        for q in quotes:
            assert 0.0 <= q.yes_bid <= q.yes_ask <= 1.0
            assert 0.0 <= q.no_bid <= q.no_ask <= 1.0


def test_generate_synthetic_history_timestamps_increase():
    history = generate_synthetic_history(n_steps=10, step_minutes=15, seed=2)
    timestamps = [t for t, _ in history]
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) == len(timestamps)


def test_generate_synthetic_history_is_deterministic_given_seed():
    history_a = generate_synthetic_history(n_steps=15, seed=42)
    history_b = generate_synthetic_history(n_steps=15, seed=42)

    prices_a = [(q.source, q.yes_bid, q.yes_ask) for _, quotes in history_a for q in quotes]
    prices_b = [(q.source, q.yes_bid, q.yes_ask) for _, quotes in history_b for q in quotes]
    assert prices_a == prices_b


def test_synthetic_history_produces_detectable_edges():
    # High mispricing rate/size makes this reliably find at least one edge
    # across enough steps, without depending on exact random values.
    history = generate_synthetic_history(n_steps=50, mispricing_prob=0.5, mispricing_size=0.1, seed=5)

    found_any = False
    for _, quotes in history:
        cross_edges = edge.find_cross_platform_edges("g", quotes, min_edge=0.01)
        complementary_edges = edge.find_complementary_edges("g", quotes, min_edge=0.01)
        if cross_edges or complementary_edges:
            found_any = True
            break

    assert found_any
