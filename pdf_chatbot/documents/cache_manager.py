LOOKUP = {}


class DocCacheManager:

    def add(self, key: str, value: dict):
        LOOKUP[key] = value

    def get(self, key):
        if key in LOOKUP:
            return LOOKUP[key]
        return None

    def get_all_chunks(self, file_hash_list: list[str]):
        file_hash_list = file_hash_list or LOOKUP.keys()
        chunks = []
        for key, val in LOOKUP.items():
            if key in file_hash_list:
                chunks.extend(val["chunks"])
        return chunks
