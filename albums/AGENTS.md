# Album Guidance

The [root guidance](../AGENTS.md) also applies.

- Put album mutations in [services.py](services.py), not directly in views,
  forms or admin actions. Keep service functions independent of HTTP responses.
- Scope every lookup and mutation to the authenticated, active owner. UUIDs do
  not replace authorisation; another user's album must not be disclosed.
- Only unexpired drafts are editable. Do not revive expired albums by renewing
  retention before checking expiry.
- Preserve the atomic version predicate for updates and deletes. Increment the
  version on a successful mutation, reject stale requests and expose a recovery
  action in the UI. Do not replace this with an unconditional `save()`.
- A transaction or `select_for_update()` alone does not establish equivalent
  concurrency behaviour on SQLite and PostgreSQL. Test simultaneous writers
  when changing transaction or locking behaviour, not just sequential retries.
- Require an active print product for new selections. Preserve the current
  product on rename even if it has since been deactivated.
- Preserve protected relationships for owners and referenced print products;
  account deletion and fulfilment retention need explicit workflows.
- Keep album admin read-only until a permission-checked, audited workflow exists.
- Mirror service coverage in request tests for ownership, stale versions,
  expiry/non-draft states, POST-only mutations and CSRF. Use the existing helpers
  in [tests/test_services.py](tests/test_services.py) and
  [tests/test_views.py](tests/test_views.py).

Run from the repository root:

```sh
uv run --env-file .env.example python manage.py test albums
```