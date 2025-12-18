LOOKUP = {}

class DocCacheManager:

    def add(self, key: str, value: dict):
        LOOKUP[key] = value

    def get(self, key):
        if key in LOOKUP:
            return LOOKUP[key]
        return None

    def get_all_chunks(self):
        chunks = []
        for key, val in LOOKUP.items():
            chunks.extend(val["chunks"])
        return chunks

