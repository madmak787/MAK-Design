# MAK Design

A personal, login-protected design workspace for **design.khanamir.me**, made for Hostinger shared PHP hosting. It uses the open-source **FigCraft 0.13.1** engine by the ArtCraft team, with original MAK floral light/dark UI tokens, a blossom icon, a MAK wordmark and a matching private project portal. The native source changes are reproducible through `scripts/theme-editor.py`; document paint and geometry logic are unchanged.

The portal uses a vibrant floral palette (hibiscus, orchid, coral and marigold) and an original SVG blossom monogram in `public/logo.svg`, licensed with the portal additions.

## Features

- A compact floral file browser with sidebar navigation, private thumbnails, search, sorting, grid/list layouts and a client-shared view.
- A full-window editor with a compact toolbar, native layers/pages and design-property sidebars, optional browser fullscreen, and a dismissible AI drawer.
- Manual design with FigCraft's layers, frames, typography, vectors and editor tools.
- Private owner sign-in with a hashed password, secure HTTPS session cookies, CSRF protection, rate limiting and a 12-hour inactivity timeout.
- Projects stored in SQLite **outside the public web directory**. Save/reopen the active design and download an editable `.figcraft` backup. Concurrent saves detect conflicts.
- Client **PNG preview links**, revocable per project and expiring after 30 days. Clients receive the saved image, never the design archive or owner access. Saving updates the preview behind existing links. Select a frame before saving for a focused preview, or clear the selection for the current page.
- AI-assisted design through a prompt/reply handoff: copy the prompt to your AI app, paste its JSON reply and add editable layers as one undo step. No API key, automatic AI calls or paid fallback. The allowed drawing commands are listed in `public/app.js`.

This is a personal portal around an alpha editor, not a full Figma replacement. It does not add live multiplayer, interactive client prototypes, client accounts or a built-in AI model. The editor keeps its upstream licenses and credits. Its native menus, panels and selection colors use MAK branding; no endorsement by the ArtCraft team is implied. An Apache content policy prevents the hosted editor from connecting to external collaboration servers. Use the portal's **Client link** button for sharing.

New designs reuse FigCraft’s untouched startup document, rather than opening a second Untitled tab. Opening a saved design removes that blank starter only if it has no changes. Recovered and edited tabs stay open. Cloud save associations follow each native editor tab.

## Local setup

PHP 8.3+ with PDO SQLite; Python 3 for fetching the pinned editor. No Node dependencies, Rust toolchain or VPS are needed.

```sh
python3 scripts/prepare-editor.py
# Supply a strong password through stdin, never as a command argument.
php scripts/configure.php /absolute/path/outside-the-web-root
MAK_PRIVATE_DIR=/absolute/path/outside-the-web-root php -S 127.0.0.1:8873 -t public
python3 tests/api_test.py
node --test tests/editor-session.test.cjs
```

`configure.php` reads the password until stdin closes and refuses to replace existing credentials. Keep the password in your password manager. The development server does not implement `.htaccess`; test the network policy on Apache/LiteSpeed in production.

## Hostinger deployment

1. Create `design.khanamir.me` pointing at `/domains/khanamir.me/public_html/design` with HTTPS.
2. Run `python3 scripts/prepare-editor.py`, then upload `public/` contents to that directory, including hidden configuration files.
3. Provision `config.php` and SQLite storage under `/domains/khanamir.me/mak-design-private/`, **outside** `public_html`. Config returns `['password_hash' => password_hash(...)]`. The database is created on first request. Preserve this private directory on all deployments.
4. Verify sign-in, save, reopen, AI sample, client preview and revocation. Back up `mak-design-private/` regularly. A client link is a bearer credential; anyone holding it can view the preview until revoked/expired.

Deployment credentials, production password hashes and private designs are never committed to this public repository. The editor is downloaded at package time from the pinned `mak-floral-editor-v1` release of this repository, checked against SHA-256 `d3b5b3c79f0636dcecc3e08ea74b078b096d429032df3282ef1bbee25d76c1ee`. The package includes build provenance, font notices and the source patch. The build uses Rust 1.99.1, Trunk 0.22.1, upstream FigCraft commit `76f520ffaaab73fcacf14dfaf30f29272ec178cb`, and craft-fonts commit `aced4137c022f1f587624d48e81ec77e1914a9cc`. GitHub Actions remains disabled on this public repository; the first package was built locally. The checked-in build workflow records an optional reproducible build path, not a running automation.

## Credits and license

Based on [FigCraft](https://github.com/storytold/figcraft), copyright 2026 ArtCraft Team and the FigCraft contributors, dual licensed MIT OR Apache-2.0. Original notices are retained in `LICENSE-MIT`, `LICENSE-APACHE` and `NOTICE`; the prepared editor includes the upstream asset and font license notices. Upstream source remains available through the fork's `main` branch; this portal is on `codex/hostinger`.

The MAK portal additions are copyright 2026 madmak787 and licensed MIT under the terms in `LICENSE-PORTAL`. ArtCraft trademarks are not licensed by these open-source licenses and are not used as this portal's branding.
