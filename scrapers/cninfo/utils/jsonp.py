
import json, re

def strip_jsonp(s: str):
    if not s:
        return {}
    l = s.find('(')
    r = s.rfind(')')
    if l != -1 and r != -1 and r > l:
        s = s[l+1:r]
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        try:
            return json.loads(re.sub(r'^\ufeff', '', s))
        except Exception:
            return {}
