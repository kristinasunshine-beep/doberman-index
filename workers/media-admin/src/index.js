const SITE_ORIGIN = "https://doberman-index.com";

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": SITE_ORIGIN,
      "Access-Control-Allow-Headers": "Authorization, Content-Type, X-DI-Registered-Name, X-DI-Source-Url, X-DI-Role",
      "Access-Control-Allow-Methods": "GET,HEAD,PUT,DELETE,OPTIONS",
      "Vary": "Origin"
    }
  });
}

function authorized(request, env) {
  if (!env.MEDIA_ADMIN_KEY) return false;
  const auth = request.headers.get("Authorization") || "";
  return auth === "Bearer " + env.MEDIA_ADMIN_KEY;
}

function normalizeKey(pathname) {
  const prefix = "/v1/admin/media/";
  if (!pathname.startsWith(prefix)) return null;
  const raw = decodeURIComponent(pathname.slice(prefix.length)).replace(/^\/+/, "");
  if (!raw || raw.includes("..") || raw.includes("\\") || raw.length > 400) return null;
  if (!(raw.startsWith("ancestors/") || raw.startsWith("dogs/"))) return null;
  return raw;
}

function contentLimit(key, contentType) {
  if (key.endsWith(".mp4") || key.endsWith(".mov") || contentType.startsWith("video/")) {
    return 180 * 1024 * 1024;
  }
  return 20 * 1024 * 1024;
}

function publicUrl(env, key) {
  const base = (env.MEDIA_PUBLIC_BASE || "https://media.doberman-index.com").replace(/\/+$/, "");
  return base + "/" + key.split("/").map(encodeURIComponent).join("/");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": SITE_ORIGIN,
          "Access-Control-Allow-Headers": "Authorization, Content-Type, X-DI-Registered-Name, X-DI-Source-Url, X-DI-Role",
          "Access-Control-Allow-Methods": "GET,HEAD,PUT,DELETE,OPTIONS",
          "Vary": "Origin"
        }
      });
    }

    if (url.pathname === "/" || url.pathname === "/health") {
      return json({
        ok: true,
        service: "doberman-index-media-admin",
        storage: "cloudflare-r2"
      });
    }

    const key = normalizeKey(url.pathname);
    if (!key) return json({ error: "Unknown media path." }, 404);
    if (!authorized(request, env)) return json({ error: "Unauthorized." }, 401);
    if (!env.MEDIA_BUCKET) return json({ error: "R2 media bucket is not configured." }, 503);

    if (request.method === "HEAD" || request.method === "GET") {
      const object = await env.MEDIA_BUCKET.head(key);
      if (!object) return json({ exists: false, key }, 404);
      return json({
        exists: true,
        key,
        size: object.size,
        uploaded: object.uploaded,
        httpMetadata: object.httpMetadata || {},
        customMetadata: object.customMetadata || {},
        public_url: publicUrl(env, key)
      });
    }

    if (request.method === "DELETE") {
      await env.MEDIA_BUCKET.delete(key);
      return json({ deleted: true, key });
    }

    if (request.method !== "PUT") return json({ error: "Method not allowed." }, 405);

    const contentType = request.headers.get("Content-Type") || "application/octet-stream";
    const length = Number(request.headers.get("Content-Length") || 0);
    const max = contentLimit(key, contentType);
    if (length && length > max) return json({ error: "Media object is too large." }, 413);

    const body = await request.arrayBuffer();
    if (!body.byteLength) return json({ error: "Empty media object." }, 400);
    if (body.byteLength > max) return json({ error: "Media object is too large." }, 413);

    const metadata = {
      registered_name: request.headers.get("X-DI-Registered-Name") || "",
      source_url: request.headers.get("X-DI-Source-Url") || "",
      role: request.headers.get("X-DI-Role") || "",
      added_at: new Date().toISOString()
    };

    await env.MEDIA_BUCKET.put(key, body, {
      httpMetadata: {
        contentType,
        cacheControl: "public, max-age=31536000, immutable"
      },
      customMetadata: metadata
    });

    return json({
      stored: true,
      key,
      size: body.byteLength,
      public_url: publicUrl(env, key),
      metadata
    }, 201);
  }
};
