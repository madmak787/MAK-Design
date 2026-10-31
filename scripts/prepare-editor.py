"""Fetch the pinned, unmodified FigCraft editor; retain its redistributable notices."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile
import sys

VERSION = '0.13.1'
SHA256 = 'fc2cb8d8fa6b8c3846514f064fc18a5acd3a228609a5cf7332b9f6555057999c'
ROOT = Path(__file__).resolve().parents[1]
url = f'https://github.com/storytold/figcraft/releases/download/v{VERSION}/figcraft-web-{VERSION}.zip'
archive = Path(sys.argv[1]).read_bytes() if len(sys.argv) > 1 else urllib.request.urlopen(url, timeout=120).read()
if hashlib.sha256(archive).hexdigest() != SHA256:
    raise SystemExit('Editor checksum mismatch; refusing to package.')
dest = ROOT / 'public/editor'
dest.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    for item in z.infolist():
        relative = Path(*Path(item.filename).parts[1:])
        if item.is_dir() or '..' in relative.parts:
            continue
        # Do not redistribute upstream marketing pages or trademark artwork.
        if relative.name in {'README.md', 'HOSTING.md', '.htaccess', '_headers'}:
            continue
        if relative.suffix not in {'.html', '.js', '.wasm', '.txt', '.md', ''}:
            continue
        out = dest / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(z.read(item))
(dest / '.htaccess').write_text('''Options -Indexes
AddType application/wasm .wasm
<IfModule mod_headers.c>
# The personal portal does not use upstream public collaboration services.
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' blob:; font-src 'self' data:; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"
Header always set Referrer-Policy "no-referrer"
Header always set X-Content-Type-Options "nosniff"
</IfModule>
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE application/wasm text/javascript application/javascript text/html
</IfModule>
''')
print(f'FigCraft {VERSION}: checksum verified; editor and license notices prepared.')
