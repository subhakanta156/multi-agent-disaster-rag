class ShortTermMemory:
    """
    Stores per-session memory:
        - last user queries
        - last agent responses
        - context for LangGraph state
    """

    def __init__(self):
        self.buffer = []

    def add(self, interaction):
        """
        interaction = {"user": "...", "assistant": "..."}
        """
        self.buffer.append(interaction)
        if len(self.buffer) > 10:
            self.buffer.pop(0)  # keep last 10

    def get(self):
        return self.buffer

    def clear(self):
        self.buffer = []
