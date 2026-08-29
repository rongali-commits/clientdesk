# ClientDesk QA checklist

## Automated checks

- [ ] `pytest -q` passes
- [ ] `ruff check .` passes
- [ ] All three JavaScript files pass `node --check`
- [ ] `/health` returns `status: ok`

## Branding and content

- [ ] Buyer name, logo letters, colors, support email, and welcome message are correct
- [ ] No fictional Aster & Lane or Northlight data remains in production
- [ ] Client names, dates, invoices, and links were approved by the buyer
- [ ] Privacy link is correct or intentionally omitted

## Access and safety

- [ ] `APP_ENV=production`
- [ ] `SEED_DEMO_DATA=false`
- [ ] Admin token is unpredictable and at least 24 characters
- [ ] Public demo token cannot access the deployment
- [ ] Invalid portal tokens return 404
- [ ] Admin APIs return 401 without the correct token
- [ ] HTTPS is active
- [ ] Database uses a persistent volume with backups

## Client workflow

- [ ] New client workspace can be created
- [ ] Project status, progress, plan, and due date can be updated
- [ ] Milestone appears in the correct portal
- [ ] Client-facing update appears in the portal
- [ ] Deliverable opens safely in a new tab
- [ ] Approval accepts approve and request-changes decisions
- [ ] Invoice amount, currency, status, and link are correct
- [ ] Completed content displays correctly on desktop and mobile

## Delivery boundary

- [ ] Buyer understands that deliverables are links, not secure file storage
- [ ] Buyer understands that invoice entries do not process payments
- [ ] Buyer understands that private portal URLs must not be posted publicly
- [ ] Source-code and resale rights match the purchased package

