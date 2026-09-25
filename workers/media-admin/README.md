# Doberman Index Media Admin Worker

Admin-only write gateway for curated public media stored in Cloudflare R2.

## Required Cloudflare configuration

Create an R2 bucket named:

```
doberman-index-media
```

Bind it as `MEDIA_BUCKET`.

Create a Worker secret:

```
MEDIA_ADMIN_KEY
```

The Worker itself is published on the custom domain:

```
media.doberman-index.com
```

The R2 bucket remains private. Public GET/HEAD requests are served through the Worker, while writes stay behind the admin secret.

The secret must never be committed to GitHub.

## Object layout

```
ancestors/DI-A-000011/main.jpg
dogs/DI-M-000123/hero.jpg
dogs/DI-M-000123/gallery/01.jpg
dogs/DI-M-000123/movement/main.mp4
```

## API

`PUT /v1/admin/media/{key}` uploads/replaces an object.

`HEAD /v1/admin/media/{key}` or `GET` checks whether an object exists.

`DELETE /v1/admin/media/{key}` removes an object.

All media endpoints require:

```
Authorization: Bearer <MEDIA_ADMIN_KEY>
```

Optional provenance headers:

- `X-DI-Registered-Name`
- `X-DI-Source-Url`
- `X-DI-Role`


## Public reads

Public media is read directly from the same Worker domain:

```
GET https://media.doberman-index.com/dogs/DI-M-000123/gallery/01.jpg
GET https://media.doberman-index.com/ancestors/DI-A-000011/main.jpg
```

No Authorization header is needed for public reads. The underlying R2 bucket is not made public.
