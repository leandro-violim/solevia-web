# solevia-web

Public website for Solevia — deployed on Cloudflare Pages, served at solevia.app.

Kept separate from the `solevia-apps` monorepo on purpose: different release
cadence and tooling. Hosts the marketing landing page and the per-app privacy
policies required for app-store submission (e.g. `solevia.app/privacy/pop-zen`).

## Structure
```
solevia-web/
├── index.html                 # landing page
└── privacy/
    ├── pop-zen/index.html      # Pop-Zen privacy policy (placeholder)
    └── app-two/index.html      # App Two privacy policy (placeholder)
```
