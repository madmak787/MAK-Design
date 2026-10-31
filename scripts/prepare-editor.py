"""Fetch the pinned MAK floral editor build and retain upstream redistributable notices."""
import hashlib
import io
from pathlib import Path
import urllib.request
import zipfile
import sys
import calendar
import os

VERSION = '0.13.1-mak-floral-1'
SHA256 = 'd3b5b3c79f0636dcecc3e08ea74b078b096d429032df3282ef1bbee25d76c1ee'
ROOT = Path(__file__).resolve().parents[1]
url = 'https://github.com/madmak787/MAK-Design/releases/download/mak-floral-editor-v1/mak-floral-editor-v1.zip'
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
        modified=calendar.timegm((*item.date_time,0,0,0))
        os.utime(out,(modified,modified))
(dest / '.htaccess').write_text('''Options -Indexes
AddType application/wasm .wasm
<IfModule mod_headers.c>
# The personal portal does not use upstream public collaboration services.
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' blob:; font-src 'self' data:; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'self'"
Header always set Referrer-Policy "no-referrer"
Header always set X-Content-Type-Options "nosniff"
<Files "index.html">
Header always set Cache-Control "no-cache"
</Files>
</IfModule>
<IfModule mod_deflate.c>
AddOutputFilterByType DEFLATE application/wasm text/javascript application/javascript text/html
</IfModule>
''')
print(f'FigCraft {VERSION}: checksum verified; editor and license notices prepared.')
