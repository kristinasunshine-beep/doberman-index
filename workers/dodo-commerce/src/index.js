const SITE_ORIGIN = "https://doberman-index.com";
const DODO_LIVE_API = "https://live.dodopayments.com";
const DODO_TEST_API = "https://test.dodopayments.com";

const PRODUCTS = {
  "doberman-intelligence-record": {
    env: "DODO_PRODUCT_INTELLIGENCE_RECORD",
    name: "Doberman Intelligence Record"
  },
  "kennel-promotion-service": {
    env: "DODO_PRODUCT_KENNEL_PROMOTION",
    name: "Kennel Promotion Service",
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

async function readPaymentByOrderReference(env, orderReference) {
  if (!env.COMMERCE_DB || !orderReference) return null;
  return env.COMMERCE_DB.prepare(
    "SELECT payment_id, service_key, order_reference, customer_email, custom_fields_json, status, succeeded_at, updated_at FROM payments WHERE order_reference = ?"
  ).bind(orderReference).first();
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
  const customFieldResponses = payment.custom_field_responses || payment.custom_fields || null;
  const customFieldsJson = customFieldResponses ? JSON.stringify(customFieldResponses) : null;
  const kennelReference = Array.isArray(customFieldResponses)
    ? customFieldResponses.find(field => field?.key === "kennel_reference")?.value || null
    : null;
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
    kennelReference,
    now,
    serviceKey === "kennel-promotion-service"
      ? new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
      : null
  ).run();
}

function tokenBytes(length = 32) {
  const bytes = new Uint8Array(length);
  crypto.getRandomValues(bytes);
  let binary = "";
  bytes.forEach(byte => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).map(byte => byte.toString(16).padStart(2, "0")).join("");
}

function invitationAdminAuthorized(request, env) {
  const auth = request.headers.get("Authorization") || "";
  const expected = env.INVITATION_ADMIN_KEY ? "Bearer " + env.INVITATION_ADMIN_KEY : "";
  return Boolean(expected) && constantTimeEqual(auth, expected);
}

async function issueInvitations(request, env) {
  if (!invitationAdminAuthorized(request, env)) return json({ error: "Unauthorized." }, 401);
  if (!env.COMMERCE_DB) return json({ error: "Commerce database is unavailable." }, 503);

  const input = await request.json().catch(() => ({}));
  const serviceKey = String(input.service_key || "");
  if (!PRODUCTS[serviceKey]) return json({ error: "Unknown service." }, 400);

  const quantity = Math.max(1, Math.min(100, Number(input.quantity) || 1));
  const expiresInDays = Math.max(1, Math.min(365, Number(input.expires_in_days) || 30));
  const now = new Date();
  const expiresAt = new Date(now.getTime() + expiresInDays * 86400000).toISOString();
  const issued = [];

  for (let index = 0; index < quantity; index += 1) {
    const invitationId = crypto.randomUUID();
    const token = tokenBytes();
    const tokenHash = await sha256Hex(token);
    const recipientName = quantity === 1 ? String(input.recipient_name || "").trim() || null : null;
    const recipientEmail = quantity === 1 ? String(input.recipient_email || "").trim() || null : null;
    const note = String(input.note || "").trim() || null;

    await env.COMMERCE_DB.prepare(`
      INSERT INTO invitations (
        invitation_id, token_hash, service_key, recipient_name, recipient_email,
        status, note, created_at, expires_at
      ) VALUES (?, ?, ?, ?, ?, 'issued', ?, ?, ?)
    `).bind(
      invitationId, tokenHash, serviceKey, recipientName, recipientEmail,
      note, now.toISOString(), expiresAt
    ).run();

    await env.COMMERCE_DB.prepare(`
      INSERT INTO entitlements (
        entitlement_id, source_type, service_key, source_reference,
        customer_email, status, created_at, expires_at
      ) VALUES (?, 'invitation_waiver', ?, ?, ?, 'available', ?, ?)
    `).bind(
      "ent_inv_" + invitationId,
      serviceKey,
      invitationId,
      recipientEmail,
      now.toISOString(),
      expiresAt
    ).run();

    issued.push({
      invitation_id: invitationId,
      service_key: serviceKey,
      token,
      invite_url: SITE_ORIGIN + "/invite.html?token=" + encodeURIComponent(token),
      expires_at: expiresAt
    });
  }

  return json({ invitations: issued });
}

async function invitationFromToken(env, token) {
  if (!env.COMMERCE_DB || !token) return null;
  const tokenHash = await sha256Hex(token);
  return env.COMMERCE_DB.prepare(`
    SELECT invitation_id, service_key, recipient_name, recipient_email,
           status, note, created_at, expires_at, opened_at, redeemed_at, revoked_at
    FROM invitations WHERE token_hash = ?
  `).bind(tokenHash).first();
}

function invitationUsable(record) {
  if (!record) return false;
  if (record.status === "revoked" || record.status === "redeemed") return false;
  if (record.revoked_at || record.redeemed_at) return false;
  if (record.expires_at && Date.parse(record.expires_at) < Date.now()) return false;
  return record.status === "issued" || record.status === "opened";
}

async function markInvitationOpened(env, invitation) {
  if (!env.COMMERCE_DB || !invitation?.invitation_id) {
    throw new Error("Commerce database is unavailable.");
  }

  const now = new Date().toISOString();
  await env.COMMERCE_DB.prepare(`
    UPDATE invitations
    SET status = 'opened', opened_at = COALESCE(opened_at, ?)
    WHERE invitation_id = ? AND status IN ('issued', 'opened')
  `).bind(now, invitation.invitation_id).run();

  const refreshed = await env.COMMERCE_DB.prepare(`
    SELECT invitation_id, service_key, recipient_name, recipient_email,
           status, note, created_at, expires_at, opened_at, redeemed_at, revoked_at
    FROM invitations
    WHERE invitation_id = ?
  `).bind(invitation.invitation_id).first();

  if (!refreshed || refreshed.status !== "opened" || !refreshed.opened_at) {
    throw new Error("Invitation open state could not be persisted.");
  }

  return refreshed;
}

async function resolveInvitation(url, env) {
  const token = url.searchParams.get("token") || "";
  const requestedService = url.searchParams.get("service") || "";
  const invitation = await invitationFromToken(env, token);
  if (!invitationUsable(invitation)) return json({ valid: false, error: "Invitation is invalid, expired or already used." }, 404);
  if (requestedService && invitation.service_key !== requestedService) return json({ valid: false, error: "Invitation service mismatch." }, 409);

  const openedInvitation = await markInvitationOpened(env, invitation);

  return json({
    valid: true,
    invitation_id: openedInvitation.invitation_id,
    service_key: openedInvitation.service_key,
    service_name: PRODUCTS[openedInvitation.service_key]?.name || openedInvitation.service_key,
    recipient_name: openedInvitation.recipient_name,
    expires_at: openedInvitation.expires_at
  });
}

async function redeemInvitation(request, env) {
  if (!env.COMMERCE_DB) return json({ error: "Commerce database is unavailable." }, 503);
  const input = await request.json().catch(() => ({}));
  const token = String(input.token || "");
  const serviceKey = String(input.service_key || "");
  const invitation = await invitationFromToken(env, token);
  if (!invitationUsable(invitation)) return json({ error: "Invitation is invalid, expired or already used." }, 409);
  if (serviceKey && invitation.service_key !== serviceKey) return json({ error: "Invitation service mismatch." }, 409);

  const now = new Date().toISOString();
  await env.COMMERCE_DB.batch([
    env.COMMERCE_DB.prepare(
      "UPDATE invitations SET status = 'redeemed', redeemed_at = ? WHERE invitation_id = ?"
    ).bind(now, invitation.invitation_id),
    env.COMMERCE_DB.prepare(
      "UPDATE entitlements SET status = 'consumed', consumed_at = ? WHERE source_type = 'invitation_waiver' AND source_reference = ? AND service_key = ?"
    ).bind(now, invitation.invitation_id, invitation.service_key)
  ]);

  return json({ redeemed: true, invitation_id: invitation.invitation_id, service_key: invitation.service_key });
}

async function verifyAccess(url, env) {
  const serviceKey = url.searchParams.get("service") || "";
  const paymentId = url.searchParams.get("payment_id") || "";
  const orderReference = url.searchParams.get("order_reference") || url.searchParams.get("order") || "";
  const inviteToken = url.searchParams.get("invite") || "";

  if (!PRODUCTS[serviceKey]) return json({ valid: false, error: "Unknown service." }, 400);

  if (inviteToken) {
    const invitation = await invitationFromToken(env, inviteToken);
    if (!invitationUsable(invitation) || invitation.service_key !== serviceKey) {
      return json({ valid: false, error: "Invitation is unavailable." }, 403);
    }

    const openedInvitation = await markInvitationOpened(env, invitation);

    return json({
      valid: true,
      source_type: "invitation_waiver",
      source_reference: openedInvitation.invitation_id,
      invitation_id: openedInvitation.invitation_id,
      service_key: serviceKey,
      recipient_name: openedInvitation.recipient_name
    });
  }

  if (paymentId || orderReference) {
    const payment = paymentId
      ? await readStoredPayment(env, paymentId)
      : await readPaymentByOrderReference(env, orderReference);

    if (payment) {
      const entitlement = env.COMMERCE_DB ? await env.COMMERCE_DB.prepare(`
        SELECT entitlement_id, status FROM entitlements
        WHERE source_type = 'paid_dodo' AND source_reference = ? AND service_key = ?
      `).bind(payment.payment_id, serviceKey).first() : null;

      if (
        payment.status === "succeeded" &&
        entitlement?.status === "available" &&
        payment.service_key === serviceKey
      ) {
        return json({
          valid: true,
          source_type: "paid_dodo",
          source_reference: payment.payment_id,
          order_reference: payment.order_reference,
          service_key: serviceKey,
          customer_email: payment.customer_email || null
        });
      }
    }
  }

  return json({ valid: false, error: "A confirmed order or private invitation is required." }, 403);
}

async function consumePaidEntitlement(request, env) {
  if (!env.COMMERCE_DB) return json({ error: "Commerce database is unavailable." }, 503);

  const input = await request.json().catch(() => ({}));
  const paymentId = String(input.payment_id || "");
  const orderReference = String(input.order_reference || input.order || "");
  const serviceKey = String(input.service_key || "");

  if ((!paymentId && !orderReference) || !PRODUCTS[serviceKey]) {
    return json({ error: "Order and service are required." }, 400);
  }

  const payment = paymentId
    ? await readStoredPayment(env, paymentId)
    : await readPaymentByOrderReference(env, orderReference);

  if (!payment || payment.status !== "succeeded" || payment.service_key !== serviceKey) {
    return json({ error: "Confirmed payment not found." }, 403);
  }

  const resolvedPaymentId = payment.payment_id;
  const now = new Date().toISOString();

  const result = await env.COMMERCE_DB.prepare(`
    UPDATE entitlements SET status = 'consumed', consumed_at = ?
    WHERE source_type = 'paid_dodo'
      AND source_reference = ?
      AND service_key = ?
      AND status = 'available'
  `).bind(now, resolvedPaymentId, serviceKey).run();

  return json({
    consumed: Boolean(result.meta?.changes),
    payment_id: resolvedPaymentId,
    service_key: serviceKey
  });
}

async function createCheckout(request, env) {
  const input = await request.json().catch(() => ({}));
  const serviceKey = String(input.service_key || "");
  const customerEmail = String(input.customer_email || "").trim();
  const product = PRODUCTS[serviceKey];

  if (!product) return json({ error: "Unknown service." }, 400);
  if (!/^\S+@\S+\.\S+$/.test(customerEmail)) {
    return json({ error: "A valid customer email is required." }, 400);
  }

  const productId = env[product.env];
  if (!productId) return json({ error: "This service is not yet activated in Dodo Payments." }, 503);
  if (!env.DODO_PAYMENTS_API_KEY) return json({ error: "Commerce API is not configured." }, 503);

  const orderReference = crypto.randomUUID();

  const payload = {
    product_cart: [{ product_id: productId, quantity: 1 }],
    billing_currency: "EUR",
    customer: { email: customerEmail },
    return_url:
      SITE_ORIGIN +
      "/checkout-success.html?service=" +
      encodeURIComponent(serviceKey) +
      "&order_reference=" +
      encodeURIComponent(orderReference),
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
    return json({
      error: body.message || body.error || "Dodo checkout session could not be created."
    }, 502);
  }

  return json({
    checkout_url: body.checkout_url,
    session_id: body.session_id,
    order_reference: orderReference
  });
}

async function paymentStatus(url, env) {
  const paymentId = url.searchParams.get("payment_id") || "";
  const orderReference = url.searchParams.get("order_reference") || "";
  const serviceKey = url.searchParams.get("service") || "";

  if (orderReference && env.COMMERCE_DB) {
    const stored = await env.COMMERCE_DB.prepare(
      "SELECT payment_id, service_key, order_reference, customer_email, status FROM payments WHERE order_reference = ?"
    ).bind(orderReference).first();

    if (stored) {
      if (serviceKey && stored.service_key !== serviceKey) {
        return json({ error: "Service mismatch." }, 409);
      }

      return json({
        status: stored.status,
        payment_id: stored.payment_id,
        order_reference: stored.order_reference,
        service_key: stored.service_key
      });
    }

    return json({
      status: "pending",
      order_reference: orderReference,
      service_key: serviceKey
    }, 202);
  }

  if (!paymentId) {
    return json({ error: "payment_id or order_reference is required." }, 400);
  }

  const stored = await readStoredPayment(env, paymentId);

  if (stored && (!serviceKey || stored.service_key === serviceKey)) {
    return json({
      status: stored.status,
      payment_id: paymentId,
      service_key: stored.service_key
    });
  }

  const response = await fetch(
    apiBase(env) + "/payments/" + encodeURIComponent(paymentId),
    {
      headers: {
        "Authorization": "Bearer " + env.DODO_PAYMENTS_API_KEY
      }
    }
  );

  const payment = await response.json().catch(() => ({}));

  if (!response.ok) {
    return json({ error: "Payment could not be verified." }, 502);
  }

  const actualService = payment.metadata?.service_key || "";
  const status = String(payment.status || "").toLowerCase();

  if (serviceKey && actualService && actualService !== serviceKey) {
    return json({ error: "Service mismatch." }, 409);
  }

  return json({
    status,
    payment_id: paymentId,
    service_key: actualService
  });
}

async function updatePaymentLifecycle(env, paymentId, status) {
  if (!env.COMMERCE_DB || !paymentId) return;

  const now = new Date().toISOString();

  await env.COMMERCE_DB.prepare(
    "UPDATE payments SET status = ?, updated_at = ? WHERE payment_id = ?"
  ).bind(status, now, paymentId).run();

  if (["refunded", "disputed"].includes(status)) {
    await env.COMMERCE_DB.prepare(
      "UPDATE entitlements SET status = ? WHERE source_type = 'paid_dodo' AND source_reference = ?"
    ).bind(status, paymentId).run();
  }
}

async function sendBrandedPaymentEmail(env, payment) {
  if (!env.SENDGRID_API_KEY) return { skipped: true, reason: "sendgrid_not_configured" };

  const customerEmail = payment?.customer?.email || null;
  const serviceKey = payment?.metadata?.service_key || "";
  const orderReference = payment?.metadata?.order_reference || "";
  const serviceName = PRODUCTS[serviceKey]?.name || "DOBERMAN INDEX service";

  if (!customerEmail) return { skipped: true, reason: "customer_email_missing" };

  const fromEmail = env.SENDGRID_FROM_EMAIL || "dobermanindex.records@gmail.com";
  const fromName = env.SENDGRID_FROM_NAME || "DOBERMAN INDEX";
  const supportEmail = env.SUPPORT_EMAIL || "dobermanindex.records@gmail.com";

  let ctaUrl = SITE_ORIGIN;
  let ctaLabel = "Return to DOBERMAN INDEX";
  let intro = "Your payment has been confirmed and your order is ready for the next step.";

  if (serviceKey === "doberman-intelligence-record") {
    ctaUrl = SITE_ORIGIN + "/submit.html?order_reference=" + encodeURIComponent(orderReference);
    ctaLabel = "START INTELLIGENCE RECORD";
    intro = "Your payment has been confirmed. Your Doberman Intelligence Record is ready for the owner questionnaire and evidence submission.";
  } else if (serviceKey === "kennel-promotion-service") {
    ctaUrl = SITE_ORIGIN + "/submit-kennel.html?order_reference=" + encodeURIComponent(orderReference);
    ctaLabel = "START KENNEL PROMOTION";
    intro = "Your payment has been confirmed. Your 12-month Kennel Promotion is ready for the kennel information required for activation.";
  }

  const subject = "PAYMENT CONFIRMED · " + serviceName.toUpperCase();

  const html = `<!doctype html>
<html>
<body style="margin:0;background:#0d0d0d;font-family:Arial,Helvetica,sans-serif;color:#ffffff">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#0d0d0d;padding:32px 16px">
    <tr><td align="center">
      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#151515;border:1px solid #2d2d2d;border-radius:22px;overflow:hidden">
        <tr><td style="padding:34px 38px 18px;font-size:12px;letter-spacing:2px;font-weight:700;color:#f3fe19">DOBERMAN INDEX</td></tr>
        <tr><td style="padding:0 38px 14px;font-size:42px;line-height:1;font-weight:800">PAYMENT CONFIRMED.</td></tr>
        <tr><td style="padding:8px 38px 10px;font-size:17px;line-height:1.6;color:#c8c8c8">${intro}</td></tr>
        <tr><td style="padding:18px 38px;color:#ffffff">
          <div style="padding:18px 0;border-top:1px solid #333;border-bottom:1px solid #333">
            <div style="font-size:12px;color:#8f8f8f;margin-bottom:8px">SERVICE</div>
            <div style="font-size:18px;font-weight:700">${serviceName}</div>
            <div style="font-size:12px;color:#8f8f8f;margin-top:10px">ORDER REFERENCE</div>
            <div style="font-size:13px;color:#c8c8c8">${orderReference || "—"}</div>
          </div>
        </td></tr>
        <tr><td style="padding:8px 38px 34px">
          <a href="${ctaUrl}" style="display:inline-block;background:#f3fe19;color:#111111;text-decoration:none;font-weight:800;padding:16px 22px;border-radius:999px">${ctaLabel}</a>
        </td></tr>
        <tr><td style="padding:22px 38px 34px;border-top:1px solid #2d2d2d;font-size:12px;line-height:1.6;color:#8f8f8f">
          Questions about your order: <a href="mailto:${supportEmail}" style="color:#ffffff">${supportEmail}</a>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;

  const textBody =
    "DOBERMAN INDEX\n\nPAYMENT CONFIRMED.\n\n" +
    intro + "\n\nService: " + serviceName +
    "\nOrder reference: " + (orderReference || "—") +
    "\n\nNext step: " + ctaUrl +
    "\n\nQuestions: " + supportEmail;

  const response = await fetch("https://api.sendgrid.com/v3/mail/send", {
    method: "POST",
    headers: {
      "Authorization": "Bearer " + env.SENDGRID_API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: customerEmail }], subject }],
      from: { email: fromEmail, name: fromName },
      reply_to: { email: supportEmail, name: "DOBERMAN INDEX" },
      content: [
        { type: "text/plain", value: textBody },
        { type: "text/html", value: html }
      ]
    })
  });

  if (!response.ok) {
    const details = await response.text().catch(() => "");
    console.error("DOBERMAN INDEX confirmation email failed", response.status, details);
    return { sent: false, status: response.status };
  }

  return { sent: true };
}

function eventPaymentId(data) {
  return data?.payment_id || data?.payment?.payment_id || data?.payment?.id || null;
}

async function webhook(request, env) {
  const rawBody = await request.text();
  const valid = await verifyWebhook(request, rawBody, env);

  if (!valid) {
    return json({ error: "Invalid webhook signature." }, 401);
  }

  const webhookId = request.headers.get("webhook-id");
  const event = JSON.parse(rawBody);
  const eventMemory = await rememberWebhook(env, webhookId, event.type);

  if (eventMemory.duplicate) {
    return json({ received: true, duplicate: true });
  }

  if (event.type === "payment.succeeded") {
    await upsertPayment(env, event.data || {}, event.timestamp || null);
    await sendBrandedPaymentEmail(env, event.data || {});
  } else if (event.type === "payment.failed") {
    const payment = event.data || {};
    const paymentId = payment.payment_id || payment.id || null;

    if (paymentId && env.COMMERCE_DB) {
      const now = new Date().toISOString();

      await env.COMMERCE_DB.prepare(`
        INSERT INTO payments (
          payment_id, service_key, order_reference, customer_email,
          custom_fields_json, status, succeeded_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 'failed', NULL, ?)
        ON CONFLICT(payment_id) DO UPDATE SET
          status = 'failed',
          updated_at = excluded.updated_at
      `).bind(
        paymentId,
        payment.metadata?.service_key || "",
        payment.metadata?.order_reference || null,
        payment.customer?.email || null,
        (payment.custom_field_responses || payment.custom_fields)
          ? JSON.stringify(payment.custom_field_responses || payment.custom_fields)
          : null,
        now
      ).run();
    }
  } else if (event.type === "refund.succeeded") {
    await updatePaymentLifecycle(
      env,
      eventPaymentId(event.data || {}),
      "refunded"
    );
  } else if (event.type === "dispute.opened") {
    await updatePaymentLifecycle(
      env,
      eventPaymentId(event.data || {}),
      "disputed"
    );
  }

  return json({ received: true });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: corsHeaders
      });
    }

    if (
      url.pathname === "/v1/commerce/checkout" &&
      request.method === "POST"
    ) {
      return createCheckout(request, env);
    }

    if (
      url.pathname === "/v1/commerce/status" &&
      request.method === "GET"
    ) {
      return paymentStatus(url, env);
    }

    if (
      url.pathname === "/v1/commerce/webhook" &&
      request.method === "POST"
    ) {
      return webhook(request, env);
    }

    if (
      url.pathname === "/v1/commerce/access" &&
      request.method === "GET"
    ) {
      return verifyAccess(url, env);
    }

    if (
      url.pathname === "/v1/commerce/consume" &&
      request.method === "POST"
    ) {
      return consumePaidEntitlement(request, env);
    }

    if (
      url.pathname === "/v1/invitations/issue" &&
      request.method === "POST"
    ) {
      return issueInvitations(request, env);
    }

    if (
      url.pathname === "/v1/invitations/resolve" &&
      request.method === "GET"
    ) {
      return resolveInvitation(url, env);
    }

    if (
      url.pathname === "/v1/invitations/redeem" &&
      request.method === "POST"
    ) {
      return redeemInvitation(request, env);
    }

    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (path === "/" || path === "/health") {
      return json({
        ok: true,
        service: "doberman-index-commerce",
        provider: "dodo_payments",
        environment: env.DODO_PAYMENTS_ENVIRONMENT || "live_mode"
      });
    }

    return json({
      error: "Not found.",
      path: url.pathname
    }, 404);
  }
};
