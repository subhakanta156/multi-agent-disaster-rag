import json
import os

class LongTermMemory:
    """
    Stores persistent memories (saved to disk).
    Useful for:
        - user preferences
        - frequently asked knowledge
    """

    FILE_PATH = "memory_store.json"

    def __init__(self):
        if not os.path.exists(self.FILE_PATH):
            with open(self.FILE_PATH, "w") as f:
                json.dump({"memories": []}, f)

    def add(self, text: str):
        data = self._load()
        data["memories"].append(text)
        self._save(data)

    def get_all(self):
        return self._load()["memories"]

    def _load(self):
        with open(self.FILE_PATH, "r") as f:
            return json.load(f)

    def _save(self, data):
        with open(self.FILE_PATH, "w") as f:
            json.dump(data, f, indent=2)
