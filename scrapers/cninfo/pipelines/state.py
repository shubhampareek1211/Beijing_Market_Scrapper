
import os, json, time
from ..utils.hashing import stable_hash

class StateStore:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, key):
        safe = key.replace("/", "_").replace(":", "_")
        return os.path.join(self.base_dir, f"{safe}.json")

    def get(self, key):
        p = self._path(key)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def put_if_changed(self, key, obj):
        p = self._path(key)
        new_hash = stable_hash(obj)
        current = None
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                current = json.load(f)
        if not current or current.get("_hash") != new_hash:
            with open(p, "w", encoding="utf-8") as f:
                obj2 = dict(obj)
                obj2["_hash"] = new_hash
                obj2["_ts"] = time.time()
                json.dump(obj2, f, ensure_ascii=False, indent=2)
            return True
        return False
