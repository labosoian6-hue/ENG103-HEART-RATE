python3 - <<'EOF'
import hashlib
from dotenv import dotenv_values
v = dotenv_values(".env")
for k in sorted(v):
    if "DROPBOX" in k:
        s = v[k] or ""
        print(k, "len", len(s), "hash", hashlib.sha256(s.encode()).hexdigest()[:8], "clean" if s == s.strip() else "HAS EXTRA SPACES")
EOF
