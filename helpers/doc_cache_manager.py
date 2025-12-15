import json


class DocCacheManager:

    def __init__(self):
        self.lookup_file_path = "./data/document_lookup.json"
        self.lookup = {}
        with open(self.lookup_file_path, "r") as json_file:
            self.lookup = json.load(json_file)

    def add(self, key: str, value: dict):
        self.lookup[key] = value
        with open(self.lookup_file_path, "w") as json_file:
            json.dump(self.lookup, json_file, indent=2)

    def get(self, key):
        if key in self.lookup:
            return self.lookup[key]
        return None
