"""Unit tests for flafl.context."""

from flafl import context


class DummyStrategy:
    """Simple strategy used to test Context execution."""

    def __init__(self):
        self.calls = []

    def execute(self, json_data, debug_info, conns, config):
        self.calls.append((json_data, debug_info, conns, config))
        return "ok"


def test_context_uses_default_empty_config():
    strat = DummyStrategy()
    ctx = context.Context(strat)

    result = ctx.execute_strategy({"a": 1}, {"b": 2}, {"c": 3})

    assert result == "ok"
    assert strat.calls[0][3] == {}


def test_context_uses_provided_config():
    strat = DummyStrategy()
    cfg = {"x": 1}
    ctx = context.Context(strat)

    result = ctx.execute_strategy({}, {}, {}, cfg)

    assert result == "ok"
    assert strat.calls[0][3] == cfg
