# Dodo commerce architecture · launch v1

## Product truth

**Doberman Intelligence Record · €149 one time**
- permanent DI identity;
- public intelligence record;
- Evidence Ledger;
- Pedigree Intelligence;
- lineage context;
- Breeding Lens;
- future updateability.

**Kennel Promotion Service · €149 / 12 months**
- paid placement in Promoted Kennels;
- linked to the approved kennel/program destination;
- same logo area and rotation rules;
- clearly marked paid visibility.

## Flow

```
Homepage service selection
  -> Doberman Index Commerce Worker
  -> fresh Dodo Checkout Session
  -> Dodo hosted checkout
  -> Dodo payment.succeeded webhook
  -> verified return page
  -> fulfillment
     Intelligence Record -> owner submission
     Kennel Promotion -> existing DI-K activation or kennel submission when missing
```

GitHub Pages never receives the Dodo API key or webhook secret.

## State and entitlement model

Commerce state is stored in Cloudflare D1, not KV. D1 is used for:
- webhook idempotency;
- verified Dodo payment state;
- paid entitlements;
- invitation / waived entitlements;
- 12-month promotion expiry state.

The public invitation system remains outside Dodo. A free invitation creates an `invitation_waiver` entitlement that unlocks the same questionnaire and review pipeline without creating a zero-price Dodo order.

## Founding Network

Founding / waived Intelligence Records are invitation-only. They do not use a public discount and do not change the €149 public value anchor. They enter the same review, canonical record and publication workflow.

## Launch sequence

1. Create both products in Dodo dashboard with EUR and tax-inclusive pricing.
2. Copy their Dodo product IDs into Worker secrets.
3. Deploy Worker + KV.
4. Add Dodo webhook endpoint.
5. Run test-mode checkout for both products.
6. Test payment success, failure, duplicate webhook, refund, return-page refresh and wrong service/payment combinations.
7. Switch Worker to `live_mode`.
8. Merge commerce branch into `main`.
