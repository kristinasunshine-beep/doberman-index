# Doberman Index · Dodo Commerce Worker

This worker is the server-side boundary between GitHub Pages and Dodo Payments.

## Public endpoints

- `POST /v1/commerce/checkout` — creates a fresh, single-use Dodo Checkout Session.
- `GET /v1/commerce/status?payment_id=...&service=...` — verifies a returned payment server-side.
- `POST /v1/commerce/webhook` — receives signed Dodo webhooks and records successful payments.
- `GET /health` — simple deployment health check.

## Live products

Create exactly two launch products in Dodo Payments:

1. **Doberman Intelligence Record**
   - EUR 149
   - one-time payment
   - tax inclusive: ON
   - product type: digital product / productised digital service
   - env secret: `DODO_PRODUCT_INTELLIGENCE_RECORD`

2. **Kennel Promotion Service**
   - EUR 149
   - one-time payment
   - entitlement: 12 months of Promoted Kennels placement
   - tax inclusive: ON
   - env secret: `DODO_PRODUCT_KENNEL_PROMOTION`

The promotion checkout collects one required custom field: kennel DI-K ID or registered kennel name.

## Required secrets

- `DODO_PAYMENTS_API_KEY`
- `DODO_PAYMENTS_WEBHOOK_KEY`
- `DODO_PRODUCT_INTELLIGENCE_RECORD`
- `DODO_PRODUCT_KENNEL_PROMOTION`

Never commit any of these values.

## Dodo dashboard webhook

Create one endpoint:

`https://doberman-index-commerce.dobermanindex-records.workers.dev/v1/commerce/webhook`

Subscribe at minimum to:
- `payment.succeeded`
- `payment.failed`
- `refund.succeeded`
- `dispute.opened`

The worker currently persists successful payment state. Additional refund/dispute operational handling can be added before automated revocation workflows are introduced.

## Fulfillment

- Intelligence Record: verified return opens `/submit.html`.
- Kennel Promotion: verified return requires no duplicate submission for an existing approved DI-K + approved logo; otherwise it opens `/submit-kennel.html`.
- Founding Network records stay outside public checkout and use the same record standard through invitation/waiver.
