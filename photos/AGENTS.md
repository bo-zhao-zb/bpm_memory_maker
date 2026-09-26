# Photo Guidance

The [root guidance](../AGENTS.md) and [album guidance](../albums/AGENTS.md) also apply.

- Originals are immutable private assets. Generate separate previews and future
  improvements; never rewrite an original in place.
- Keep storage access behind Django's storage API and persist storage keys, not
  host filesystem paths. Never expose `MEDIA_ROOT` or a public media URL.
- Validate byte size, decoded format, dimensions, pixel count and full image
  decoding before persistence. Extensions and browser content types are untrusted.
- Generated previews must apply EXIF orientation and omit EXIF/GPS metadata.
- Reserve album capacity atomically and keep `Album.photo_count` consistent with
  photo creation/deletion. Add concurrency coverage when changing reservation logic.
- Every asset lookup must include album ownership. Downloads of originals are
  attachments; previews may be inline but remain private and non-cacheable.
- Filesystem writes are not transactional. Clean failed writes and delete files
  only after successful database deletion commits.
- Keep upload limits configurable and test JPEG, PNG, HEIC/HEIF, corrupt files,
  oversized files, decompression limits, capacity, ownership and cleanup.

Run from the repository root:

```sh
uv run --env-file .env.example python manage.py test photos
```