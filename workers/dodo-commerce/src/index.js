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
    billing_currency: "EUR",
    return_url: product.returnUrl,
    metadata: {
      order_reference: orderReference,
      service_key: serviceKey,
      source: "doberman-index.com"
    },
    feature_flags: {
      redirect_immediately: true,
      allow_tax_id: true
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

  if (env.COMMERCE_STATE && body.session_id) {
    await env.COMMERCE_STATE.put("session:" + body.session_id, JSON.stringify({
      service_key: serviceKey,
      order_reference: orderReference,
      customer_email: customerEmail,
      created_at: new Date().toISOString()
    }), { expirationTtl: 60 * 60 * 30 });
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

  if (env.COMMERCE_STATE) {
    const stored = await env.COMMERCE_STATE.get("payment:" + paymentId, "json");
    if (stored && (!serviceKey || stored.service_key === serviceKey)) {
      return json({ status: "succeeded", payment_id: paymentId, service_key: stored.service_key });
    }
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
  if (env.COMMERCE_STATE && webhookId) {
    const duplicate = await env.COMMERCE_STATE.get("webhook:" + webhookId);
    if (duplicate) return json({ received: true, duplicate: true });
    await env.COMMERCE_STATE.put("webhook:" + webhookId, "1", { expirationTtl: 60 * 60 * 24 * 30 });
  }

  const event = JSON.parse(rawBody);
  if (event.type === "payment.succeeded") {
    const payment = event.data || {};
    const paymentId = payment.payment_id || payment.id;
    const serviceKey = payment.metadata?.service_key || "";
    if (paymentId && env.COMMERCE_STATE) {
      await env.COMMERCE_STATE.put("payment:" + paymentId, JSON.stringify({
        service_key: serviceKey,
        order_reference: payment.metadata?.order_reference || null,
        customer_email: payment.customer?.email || null,
        custom_fields: payment.custom_fields || null,
        succeeded_at: event.timestamp || new Date().toISOString()
      }), { expirationTtl: 60 * 60 * 24 * 400 });
    }
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
    if (url.pathname === "/health") return json({ ok: true, provider: "dodo_payments" });
    return json({ error: "Not found." }, 404);
  }
};
