# Changelog

Notable project changes are recorded here, grouped by user or developer impact
rather than individual commits. This follows the categories used by
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Keep ongoing work under `Unreleased`. Move completed entries into a dated version
section when an explicit release is made. Local checkpoint commits and the version
in `pyproject.toml` do not, on their own, declare a release.

## [Unreleased]

### Added

- Django 5.2 LTS foundation with Python 3.12 managed by `uv`, locked dependencies,
  environment-based settings and a public liveness endpoint.
- Separate accounts, print catalogue and album apps, initial migrations and
  Django admin registration.
- Private draft album creation, viewing, renaming, print-size selection and
  confirmed deletion, with owner checks and stale-version conflict detection.
- Configurable album photo limits and expiry dates; expired and non-draft albums
  are read-only. Album administration is read-only.
- Repeatable catalogue seeding for the four planned print sizes, preserving
  administrator changes and protecting referenced products from deletion.
- Google/Facebook OAuth integration entry points through django-allauth, with
  development-only application password sign-in and no automatic email-based
  account linking.
- Responsive album and sign-in pages with local fonts, Lucide icons, decorative
  sign-in photography and a progressively enhanced password-visibility control.
- Automated tests for album ownership, validation, lifecycle rules, CSRF,
  authentication and UI rendering; CI configured for PostgreSQL 16 and SQLite.
- Remote-development setup instructions, scoped agent guidance, and a sourced
  [UK competitor benchmark](docs/competitive-benchmark.md).
- A repository structure guide and this ongoing changelog.
- A production container, release-aware health/readiness endpoints, hardened
  Compose baseline, VM deployment script and gated GitHub-to-Azure deployment workflow.
- An owner guide for Azure OIDC, ACR, Key Vault, DNS, HTTPS, VM isolation and
  Google OAuth configuration.
- Private JPEG, PNG and HEIC/HEIF uploads with decoded-image validation,
  configurable size/pixel limits, opaque storage keys and preserved originals.
- EXIF-oriented, metadata-free JPEG previews, per-file upload progress, private
  owner-checked previews/downloads and file cleanup on photo or album deletion.
- Retry-safe upload identifiers, version-checked photo removal, bounded upload
  requests and durable retry records for failed filesystem deletions.

### Changed

- Refreshed the UI with clearer navigation, charcoal controls, coral accents,
  illustrated album covers and more compact mobile metadata layouts.
- Clarified the competitor benchmark's proposed differentiation around product
  characteristics and measurable customer benefits, rather than visual branding.
- Scoped the first releasable MVP to AI assessment, reversible improvements and
  downloads while retaining printing, payment and fulfilment as the next phase.
- Isolated PostgreSQL and SQLite validation into separate CI jobs so database
  checks cannot leave shared-runner state for one another.

### Fixed

- Insufficient contrast on album cover labels and small illustrated-cover text.
- Undersized mobile sign-out target, increased to a minimum width of 44px.
- Simultaneous same-version album edits now resolve as one successful update and
  one recoverable conflict instead of exposing a SQLite database-lock error.
- Unconfigured Google and Facebook login routes now return HTTP 404 rather than
  failing with an internal server error.
- SQLite upload lock contention now returns a recoverable capacity response
  instead of exposing a database error.

### Known Limitations

- AI assessment/improvement, album archive downloads, checkout, fulfilment,
  expiry notifications and automatic expiry deletion remain unimplemented.
  Displayed expiry dates are not yet an end-to-end deletion guarantee.
- Live OAuth callbacks, public production deployment, container execution and
  PostgreSQL-specific runtime behaviour have not been verified locally. CI and
  deployment configuration are not evidence of successful cloud operation.

## Maintaining This File

- Update this file in the same change as a meaningful feature, fix, security
  change or development-workflow change.
- Use `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed` and `Security` where
  applicable. Omit empty categories and avoid duplicating Git's commit log.
- Describe shipped behaviour accurately: proposed capabilities belong in the
  plan or benchmark, not under implemented features here.
- Update known limitations when resolved and record the fix. Do not announce a
  release, create a tag or change package versions without an explicit release
  decision.