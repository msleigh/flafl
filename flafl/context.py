"""Context module for Strategy pattern."""


class Context:
    """Define the interface of interest to clients."""

    def __init__(self, strategy):
        """Maintain a reference to a Strategy object."""
        self._strategy = strategy

    def execute_strategy(self, json_data, debug_info, conns, config=None):
        """Execute wrapper for the Strategy object's execute method."""
        if config is None:
            config = {}
        return_value = self._strategy.execute(json_data, debug_info, conns, config)
        return return_value
