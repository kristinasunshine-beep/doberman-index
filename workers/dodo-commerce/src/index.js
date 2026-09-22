const SITE_ORIGIN = "https://doberman-index.com";
const DODO_LIVE_API = "https://live.dodopayments.com";
const DODO_TEST_API = "https://test.dodopayments.com";

const PRODUCTS = {
  "doberman-intelligence-record": {
    env: "DODO_PRODUCT_INTELLIGENCE_RECORD",
    name: "Doberman Intelligence Record",
    returnUrl: SITE_ORIGIN + "/checkout-success.html?service=doberman-intelligence-record"
  },
  "kennel-promotion-service": {
    env: "DODO_PRODUCT_KENNEL_PROMOTION",
    name: "Kennel Promotion Service",
    returnUrl: SITE_ORIGIN + "/checkout-success.html?service=kennel-promotion-service",
    customFields: [
      {
        key: "kennel_reference",
        label: "Kennel DI-K ID or registered kennel name",
        field_type: "text",
        required: true,
        placeholder: "DI-K-000001 or kennel name"
      }
    ]
  }
};

const corsHeaders = {
  "Access-Control-Allow-Origin": SITE_ORIGIN,
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Vary": "Origin"
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...corsHeaders }
  });
}

function apiBase(env) {
  return env.DODO_PAYMENTS_ENVIRONMENT === "test_mode" ? DODO_TEST_API : DODO_LIVE_API;
}

function constantTimeEqual(a, b) {
  if (a.length !== b.length) return false;
  let value = 0;
  for (let i = 0; i < a.length; i += 1) value |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return value === 0;
}

function base64Bytes(value) {
  const normalized = value.replace(/^whsec_/, "");
  const binary = atob(normalized);
  return Uint8Array.from(binary, c => c.charCodeAt(0));
}

async function verifyWebhook(request, rawBody, env) {
  const id = request.headers.get("webhook-id") || "";
  const timestamp = request.headers.get("webhook-timestamp") || "";
  const header = request.headers.get("webhook-signature") || "";
  if (!id || !timestamp || !header || !env.DODO_PAYMENTS_WEBHOOK_KEY) return false;

  const age = Math.abs(Math.floor(Date.now() / 1000) - Number(timestamp));
  if (!Number.isFinite(age) || age > 300) return false;

  const key = await crypto.subtle.importKey(
    "raw",
    base64Bytes(env.DODO_PAYMENTS_WEBHOOK_KEY),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const signed = new TextEncoder().encode(`${id}.${timestamp}.${rawBody}`);
  const digest = new Uint8Array(await crypto.subtle.sign("HMAC", key, signed));
  let binary = "";
  digest.forEach(byte => { binary += String.fromCharCode(byte); });
  const expected = btoa(binary);
  return header
    .split(/[ ,]+/)
    .map(value => value.replace(/^v1,?/, "").trim())
    .filter(Boolean)
    .some(value => constantTimeEqual(value, expected));
}

async function readStoredPayment(env, paymentId) {
  if (!env.COMMERCE_DB) return null;
  return env.COMMERCE_DB.prepare(
    "SELECT payment_id, service_key, order_reference, customer_email, custom_fields_json, status, succeeded_at, updated_at FROM payments WHERE payment_id = ?"
  ).bind(paymentId).first();
}

async function rememberWebhook(env, webhookId, eventType) {
  if (!env.COMMERCE_DB || !webhookId) return { duplicate: false };
  try {
    await env.COMMERCE_DB.prepare(
      "INSERT INTO webhook_events (webhook_id, event_type, received_at) VALUES (?, ?, ?)"
    ).bind(webhookId, eventType || "unknown", new Date().toISOString()).run();
    return { duplicate: false };
  } catch (error) {
    const message = String(error?.message || error);
    if (/unique|constraint/i.test(message)) return { duplicate: true };
    throw error;
  }
}

async function upsertPayment(env, payment, eventTimestamp) {
  if (!env.COMMERCE_DB) return;
  const paymentId = payment.payment_id || payment.id;
  if (!paymentId) return;
  const serviceKey = payment.metadata?.service_key || "";
  const orderReference = payment.metadata?.order_reference || null;
  const customerEmail = payment.customer?.email || null;
  const customFieldsJson = payment.custom_fields ? JSON.stringify(payment.custom_fields) : null;
  const status = String(payment.status || "succeeded").toLowerCase();
  const now = new Date().toISOString();
  const succeededAt = eventTimestamp || now;

  await env.COMMERCE_DB.prepare(`
    INSERT INTO payments (
      payment_id, service_key, order_reference, customer_email,
      custom_fields_json, status, succeeded_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(payment_id) DO UPDATE SET
      service_key = excluded.service_key,
      order_reference = excluded.order_reference,
      customer_email = excluded.customer_email,
      custom_fields_json = excluded.custom_fields_json,
      status = excluded.status,
      succeeded_at = COALESCE(payments.succeeded_at, excluded.succeeded_at),
      updated_at = excluded.updated_at
  `).bind(
    paymentId, serviceKey, orderReference, customerEmail,
    customFieldsJson, status, succeededAt, now
  ).run();

  const entitlementId = "ent_" + paymentId;
  await env.COMMERCE_DB.prepare(`
    INSERT INTO entitlements (
      entitlement_id, source_type, service_key, source_reference,
      customer_email, kennel_reference, status, created_at, expires_at, consumed_at
    ) VALUES (?, 'paid_dodo', ?, ?, ?, ?, 'available', ?, ?, NULL)
    ON CONFLICT(source_type, source_reference, service_key) DO NOTHING
  `).bind(
    entitlementId,
    serviceKey,
    paymentId,
    customerEmail,
    null,
    now,
    serviceKey === "kennel-promotion-service"
      ? new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
      : null
  ).run();
}

async function createCheckout(request, env) {
  const input = await request.json().catch(() => ({}));
  const serviceKey = String(input.service_key || "");
  const customerEmail = String(input.customer_email || "").trim();
  const product = PRODUCTS[serviceKey];
  if (!product) return json({ error: "Unknown service." }, 400);
  if (!/^\S+@\S+\.\S+$/.test(customerEmail)) return json({ error: "A valid customer email is required." }, 400);

  const productId = env[product.env];
  if (!productId) return json({ error: "This service is not yet activated in Dodo Payments." }, 503);
  if (!env.DODO_PAYMENTS_API_KEY) return json({ error: "Commerce API is not configured." }, 503);

  const orderReference = crypto.randomUUID();
  const payload = {
    product_cart: [{ product_id: productId, quantity: 1 }],
    customer: { email: customerEmail },
    return_url: product.returnUrl,
    metadata: {
      order_reference: orderReference,
      service_key: serviceKey,
      source: "doberman-index.com"
    },
    cancel_url: SITE_ORIGIN + "/#tiers",
    feature_flags: {
      redirect_immediately: true,
      allow_tax_id: true,
      allow_discount_code: false
    }
  };
  if (product.customFields) payload.custom_fields = product.customFields;

  const response = await fetch(apiBase(env) + "/checkouts", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + env.DODO_PAYMENTS_API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok || !body.checkout_url) {
    return json({ error: body.message || body.error || "Dodo checkout session could not be created." }, 502);
  }

  return json({
    checkout_url: body.checkout_url,
    session_id: body.session_id,
    order_reference: orderReference
  });
}

async function paymentStatus(url, env) {
  const paymentId = url.searchParams.get("payment_id");
  const serviceKey = url.searchParams.get("service") || "";
  if (!paymentId) return json({ error: "payment_id is required." }, 400);

  const stored = await readStoredPayment(env, paymentId);
  if (stored && stored.status === "succeeded" && (!serviceKey || stored.service_key === serviceKey)) {
    return json({ status: "succeeded", payment_id: paymentId, service_key: stored.service_key });
  }

  const response = await fetch(apiBase(env) + "/payments/" + encodeURIComponent(paymentId), {
    headers: { "Authorization": "Bearer " + env.DODO_PAYMENTS_API_KEY }
  });
  const payment = await response.json().catch(() => ({}));
  if (!response.ok) return json({ error: "Payment could not be verified." }, 502);

  const actualService = payment.metadata?.service_key || "";
  const status = String(payment.status || "").toLowerCase();
  if (serviceKey && actualService && actualService !== serviceKey) return json({ error: "Service mismatch." }, 409);
  return json({ status, payment_id: paymentId, service_key: actualService });
}

async function webhook(request, env) {
  const rawBody = await request.text();
  const valid = await verifyWebhook(request, rawBody, env);
  if (!valid) return json({ error: "Invalid webhook signature." }, 401);

  const webhookId = request.headers.get("webhook-id");
  const event = JSON.parse(rawBody);
  const eventMemory = await rememberWebhook(env, webhookId, event.type);
  if (eventMemory.duplicate) return json({ received: true, duplicate: true });

  if (event.type === "payment.succeeded") {
    await upsertPayment(env, event.data || {}, event.timestamp || null);
  }

  return json({ received: true });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
    if (url.pathname === "/v1/commerce/checkout" && request.method === "POST") return createCheckout(request, env);
    if (url.pathname === "/v1/commerce/status" && request.method === "GET") return paymentStatus(url, env);
    if (url.pathname === "/v1/commerce/webhook" && request.method === "POST") return webhook(request, env);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    if (path === "/" || path === "/health") {
      return json({
        ok: true,
        service: "doberman-index-commerce",
        provider: "dodo_payments",
        environment: env.DODO_PAYMENTS_ENVIRONMENT || "live_mode"
      });
    }
    return json({ error: "Not found.", path: url.pathname }, 404);
  }
};
