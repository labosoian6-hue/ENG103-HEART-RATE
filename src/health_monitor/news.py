python3 - <<'EOF'
import hashlib
from dotenv import dotenv_values
v = dotenv_values(".env")
for k in sorted(v):
    if "DROPBOX" in k:
        s = v[k] or ""
        print(k, "len", len(s), "hash", hashlib.sha256(s.encode()).hexdigest()[:8], "clean" if s == s.strip() else "HAS EXTRA SPACES")
EOF
DROPBOX_APP_KEY=krso9o3ztjrun57
DROPBOX_APP_SECRET=ht61c7o6jbxzlqk
DROPBOX_REFRESH_TOKEN=HS5KSl6IELMAAAAAAAAAAbQmWT7j7kfLdzOAotFUZ1cbcStzPYW4iuCXoTUj-74D
