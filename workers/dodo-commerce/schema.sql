PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS webhook_events (
  webhook_id TEXT PRIMARY KEY,
  event_type TEXT NOT NULL,
  received_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
  payment_id TEXT PRIMARY KEY,
  service_key TEXT NOT NULL,
  order_reference TEXT,
  customer_email TEXT,
  custom_fields_json TEXT,
  status TEXT NOT NULL,
  succeeded_at TEXT,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS payments_service_key_idx
  ON payments(service_key);

CREATE TABLE IF NOT EXISTS entitlements (
  entitlement_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL CHECK(source_type IN ('paid_dodo','invitation_waiver')),
  service_key TEXT NOT NULL,
  source_reference TEXT NOT NULL,
  customer_email TEXT,
  kennel_reference TEXT,
  status TEXT NOT NULL DEFAULT 'available',
  created_at TEXT NOT NULL,
  expires_at TEXT,
  consumed_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS entitlements_source_unique
  ON entitlements(source_type, source_reference, service_key);

CREATE TABLE IF NOT EXISTS invitations (
  invitation_id TEXT PRIMARY KEY,
  token_hash TEXT NOT NULL UNIQUE,
  service_key TEXT NOT NULL,
  recipient_name TEXT,
  recipient_email TEXT,
  status TEXT NOT NULL DEFAULT 'issued',
  note TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT,
  opened_at TEXT,
  redeemed_at TEXT,
  revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS invitations_service_status_idx
  ON invitations(service_key, status);
