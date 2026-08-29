# ClientDesk fulfillment playbook

## 1. Confirm the package

Document the number of configured workspaces, branding, deployment responsibility, revision count, source-code rights, and any excluded integrations.

## 2. Review buyer content

Check every business name, email, color, milestone, deliverable link, invoice reference, and client-facing statement. Do not invent business claims or privacy wording.

## 3. Prepare a clean deployment

- Use a new database.
- Set `SEED_DEMO_DATA=false`.
- Generate a strong private admin token.
- Set `APP_ENV=production`.
- Configure persistent storage.
- Apply buyer-approved branding.

## 4. Configure the initial workspace

Create the agreed client portal, then add its project status, due date, milestones, updates, approvals, deliverables, and invoice records.

## 5. Test privately

Run automated tests and the QA checklist. Test the private link in a separate browser profile without exposing the admin token.

## 6. Buyer preview

Send the preview through the marketplace. Ask the buyer to test with fictional data and send one consolidated revision list.

## 7. Deploy and hand off

Use buyer-owned infrastructure when included. Deliver the public product URL, admin URL, private first-client link, access method, documentation, and backup instructions.

## 8. Close responsibly

Confirm that the acceptance checks passed. Explain the support boundary and ask for an honest review only after delivery.

