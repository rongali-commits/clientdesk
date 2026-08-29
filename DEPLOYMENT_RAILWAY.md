# Deploy ClientDesk on Railway

## 1. Create the service

Deploy this repository with the included Dockerfile. Use a dedicated service for each buyer rather than mixing unrelated businesses in one database.

## 2. Add a persistent volume

Mount a Railway volume at `/app/runtime` and set:

```text
DATABASE_PATH=/app/runtime/clientdesk.db
```

## 3. Set production variables

```text
APP_ENV=production
ADMIN_TOKEN=GENERATE_A_LONG_RANDOM_SECRET
DATABASE_PATH=/app/runtime/clientdesk.db
BUSINESS_FILE=/app/data/business.json
SEED_DEMO_DATA=false
```

Railway supplies `PORT` automatically.

## 4. Verify deployment

- Open `/health` and confirm storage is `ok`.
- Confirm `/admin` rejects the demo token.
- Sign in with the private admin token.
- Create one fictional test workspace.
- Open its private portal link.
- Test progress, milestone, update, approval, deliverable, and invoice workflows.
- Remove the fictional test content before buyer handoff.

## 5. Connect the buyer domain

Add the buyer-approved custom domain in Railway, then apply the exact DNS record Railway provides. Wait for HTTPS to become active before sharing portal links.

## 6. Backups

Configure a regular backup or volume snapshot process. Download and test a database copy before major upgrades.

