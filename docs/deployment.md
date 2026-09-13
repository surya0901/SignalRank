# Deployment

## Public demo

Publication is being verified. The expected address is
`https://signalrank-surya.elated-olm-8913.chatgpt.site`.
An expected address is not proof of a successful deployment. The deployment receipt will
be recorded here after the hosting service confirms success.

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
