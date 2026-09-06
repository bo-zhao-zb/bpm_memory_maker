# Account Guidance

The [root guidance](../AGENTS.md) also applies.

- Preserve [User](models.py) as the custom user model. Use `get_user_model()`
  at runtime and `settings.AUTH_USER_MODEL` for relationships rather than
  importing Django's concrete default user model.
- Reuse django-allauth for OAuth state, callbacks and social identities; do not
  introduce a second identity table or hand-roll the OAuth exchange.
- Application password sign-in is development-only. Keep the `DEBUG` check in
  [SignInView](views.py) and the matching visibility check in the login template.
  Django admin's separate password login is not subject to that restriction;
  production admin MFA/access restrictions remain pending.
- Keep provider credentials server-side. Each provider's client ID and secret
  must be supplied together; preserve Google PKCE when changing configuration.
- Do not auto-link accounts or authenticate an existing account merely because
  email addresses match. Linking requires verified control of both identities.
- Keep social token storage disabled unless a specific approved feature needs
  it. Never log credentials, tokens or complete authentication callback URLs.
- In [settings](../config/settings.py), django-allauth social-only mode requires
  `ACCOUNT_EMAIL_VERIFICATION = "none"`. Do not infer verified ownership of an
  arbitrary email address from that setting.
- OAuth initiation and logout must remain CSRF-protected POST actions. Preserve
  Django's safe redirect handling and inactive-account checks.
- Test configured and unavailable providers, inactive users, external `next`
  URLs and development-only login. Mocked initiation does not verify live
  callbacks, new-account creation or account-linking behaviour.

Run from the repository root:

```sh
uv run --env-file .env.example python manage.py test accounts
```