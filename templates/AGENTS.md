# Template Guidance

The [root guidance](../AGENTS.md) also applies.

- Extend [base.html](base.html) and reuse
  [components/form_fields.html](components/form_fields.html) and
  [components/icon.html](components/icon.html). Use named Django URLs and the
  static template tag instead of hard-coded application or asset paths.
- Keep business rules and database queries out of templates. Hiding a control
  is not authorisation; the corresponding view and service must enforce it.
- Preserve autoescaping for album names, account details and validation errors.
  Do not apply `safe` to user content.
- Include CSRF tokens in every local POST form, including sign-in, sign-out and
  provider initiation. Preserve hidden version fields and the explicit delete
  confirmation. GET requests must not mutate application data.
- Keep labels associated with inputs, errors visible and accessible, keyboard
  focus visible, and status messages understandable without relying on colour.
  Icon-only controls need an accessible name and a tooltip.
- Use the existing local DM Sans fonts and Lucide assets in
  [static/vendor](../static/vendor). Keep licence notices and avoid introducing
  external CDN requests or a frontend build pipeline.
- Follow [app.css](../static/css/app.css): restrained album-management screens,
  responsive constraints, stable icon dimensions and wrapping for long names.
  Do not add controls that imply uploads, AI or checkout already work.
- After UI changes, run the relevant request tests and browser-check desktop
  and narrow mobile layouts, long names, validation failures and destructive
  confirmation. Verify local assets load and no controls overlap.
- Use disposable test identities for browser checks; remove only the data you
  created, and do not leave a shared password or a production login bypass.

Run from the repository root:

```sh
uv run --env-file .env.example python manage.py test accounts albums.tests.test_views
```