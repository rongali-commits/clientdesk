# ClientDesk

ClientDesk is a white-label client onboarding, project progress, approval, delivery, and invoice portal for agencies, consultants, and independent service businesses.

The included fictional **Aster & Lane Studio** experience is a safe marketplace demo. Replace every sample identity, project, link, invoice, date, claim, and contact detail with buyer-approved information before launch.

## Why this product is sellable

- It solves a visible operations problem: client work is scattered across email and disconnected links.
- Agencies can understand the value in under a minute.
- It does not require a paid AI API.
- Each buyer receives a branded, single-business deployment and private client links.
- The reusable setup makes customization fast and predictable.
- It expands the Noerong catalog beyond lead and review products.

## Included features

- Branded product landing page
- Private token-based portal for every client
- Project status, progress, plan, and target date
- Milestone roadmap
- Client-facing project updates
- Deliverable library for documents, previews, videos, and links
- Focused approval and change-request workflow
- Invoice status and optional buyer-owned payment links
- Studio dashboard with portfolio-level metrics
- Client workspace creation and management
- White-label business name, colors, support email, and welcome copy
- Read-only public demonstration mode
- Token-protected administrative APIs
- SQLite persistence for a focused single-business deployment
- Docker and Railway deployment configuration
- Tests, client intake, fulfillment, QA, delivery, and marketplace copy

## Quick start

Python 3.11 or newer is required.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
$env:ADMIN_TOKEN="choose-a-private-admin-token"
uvicorn clientdesk.app:app --reload
```

Open:

- Product page: `http://127.0.0.1:8000/`
- Studio dashboard: `http://127.0.0.1:8000/admin`
- Health check: `http://127.0.0.1:8000/health`

The public demo uses `clientdesk-demo-view` for read-only studio access. Never use that value as a production admin token.

## Safe demonstration mode

`SEED_DEMO_DATA=true` creates fictional client work, exposes the fictional portal from the product page, and makes client approval submissions non-persistent. The studio demo token allows only protected `GET` requests.

For a buyer deployment:

1. Set `SEED_DEMO_DATA=false`.
2. Generate an unpredictable admin token with at least 24 characters.
3. Replace the business configuration.
4. deploy with a persistent runtime volume.
5. Create the buyer's first client workspace from the protected dashboard.
6. Share private portal links only with their intended clients.

## Environment variables

| Variable | Required | Purpose |
| --- | ---: | --- |
| `APP_ENV` | Production | Enables strict secret validation when set to `production` |
| `ADMIN_TOKEN` | Production | Protects administrative reads and writes |
| `DATABASE_PATH` | No | SQLite path, defaults to `runtime/clientdesk.db` |
| `BUSINESS_FILE` | No | First-run white-label brand configuration |
| `SEED_DEMO_DATA` | No | Creates fictional read-only demonstration data |
| `PORT` | Hosting | Injected by Railway and similar platforms |

## Security and product boundaries

- Client portal URLs contain high-entropy access tokens and must be treated as private links.
- The admin token belongs only in a server environment variable and the studio login screen.
- Use HTTPS for every public deployment.
- Do not place API keys, passwords, payment-card data, government IDs, health records, or sensitive financial records in portal updates.
- Deliverables are links. ClientDesk does not provide encrypted file storage.
- Invoice entries are status records and optional payment links. ClientDesk does not process payments.
- SQLite is appropriate for one small agency deployment. Move to PostgreSQL and full user authentication before serving many businesses from one shared instance.
- Token links are designed for low-risk client collaboration, not regulated or enterprise identity requirements.
- Configure backups for the persistent database volume.

## Quality commands

```powershell
pytest -q
ruff check .
node --check src/clientdesk/static/landing.js
node --check src/clientdesk/static/portal.js
node --check src/clientdesk/static/admin.js
```

## Delivery documents

- [CLIENT_QUESTIONNAIRE.md](CLIENT_QUESTIONNAIRE.md)
- [FULFILLMENT_PLAYBOOK.md](FULFILLMENT_PLAYBOOK.md)
- [QA_CHECKLIST.md](QA_CHECKLIST.md)
- [DELIVERY_GUIDE.md](DELIVERY_GUIDE.md)
- [DEPLOYMENT_RAILWAY.md](DEPLOYMENT_RAILWAY.md)
- [COMMERCIAL_LICENSE_TEMPLATE.md](COMMERCIAL_LICENSE_TEMPLATE.md)
- [Upwork Project Catalog copy](sales-assets/UPWORK_PROJECT_CATALOG.md)
- [Fiverr Gig copy](sales-assets/FIVERR_GIG.md)
- [Contra service copy](sales-assets/CONTRA_SERVICE.md)

## Commercial use

This repository is a productized-service base, not a public open-source template. Customize the license for each buyer. The included template is not legal advice.

