# Deployment

## Public demo

[Open SignalRank](https://signalrank-surya.sg1670.chatgpt.site). Public access was verified on September 13, 2026.

The hosting service confirmed the first deployment succeeded at 18:51:29 UTC.
An unauthenticated HTTPS check retrieved the application HTML, JavaScript, CSS, and
9,742-movie model catalog with HTTP 200. No login cookie or bypass token was used.

Initial release receipt:
- Source: `cfd1dd93d0df7d5846d19a4a1b449fdd7ef43f6f`
- Version: 1
- Deployment: `appgdep_6aa6f0499ca0819199fc816faa66c677`

This is a static React demo with browser ranking using the scikit-learn-generated artifact.
Each visitor's ratings, likes, saves, and genre choices remain in their browser. It does not
host a Python API or PostgreSQL database. The Model page displays this mode.

## Full-stack application

The FastAPI/PostgreSQL/Nginx version is tested locally through Docker Compose. It is not
publicly deployed. Deploying those services would require a Python/container hosting account
and managed PostgreSQL (or a suitable VM), plus credentials, domain/HTTPS, backups, and
operational configuration. No account purchase or infrastructure charge has been initiated.

## Reproducibility

Run `npm --prefix frontend ci` followed by `npm run build` to reproduce the portable build.
The root build sets `VITE_PORTABLE_DEMO=true`; Compose's frontend build leaves it disabled.
Model metadata and raw measured evaluation are versioned with the source. Public access
must be explicitly enabled for portfolio visitors; an owner-private preview is not sufficient.
