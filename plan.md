# Photo Printing Website Plan

## 1. Product Goal

Build a simple, trustworthy service that lets people upload photos, organize them into an album, improve selected images with AI, choose print sizes, and submit a print order.

The first release will be a responsive website for desktop and mobile browsers. A native mobile app may be added later, so business logic should not depend on server-rendered pages even though they are the simplest choice for the first release.

## 2. Product Principles

- Keep the main journey short: sign in, create an album, upload, review, and submit.
- Preserve every original photo. AI changes must be optional, previewable, and reversible.
- Explain photo retention and AI processing before upload.
- Show progress and useful recovery actions for uploads and background processing.
- Prefer a small modular monolith over microservices for the first release.
- Make limits, print products, retention periods, and AI providers configurable.

## 3. MVP Scope

### In scope

- Responsive desktop and mobile web interface.
- Sign-in with Google and Facebook.
- Create, rename, open, and delete draft albums.
- Set one default print size per album and override it per photo.
- Upload multiple photos with per-file progress and clear validation errors.
- Review uploaded photos in a responsive thumbnail grid with AI scores and concise assessment summaries.
- Open a photo in a large viewer with its detailed assessment in a side panel.
- Reorder and remove photos before submission.
- Asynchronous AI quality assessment for each photo.
- Optional AI improvement of one or more selected photos.
- Optional conversion of selected photos into short AI-generated animations.
- Side-by-side preview with accept or reject before an improved image is used.
- Automatic print cropping with manual adjustment and reset.
- UK delivery, GBP pricing, VAT display, and hosted payment checkout.
- Final order review and submission.
- Durable order record and reliable handoff to one UK print provider.
- Automatic photo expiry and deletion after a configurable retention period.
- Basic administration for accounts, albums, print products, limits, orders, retention, and failed jobs.

### Out of scope until explicitly chosen

- Native iOS or Android apps.
- A full manual photo editor.
- Social sharing or collaborative albums.
- Multiple print providers.
- Permanent photo storage.
- Advanced animation editing or using animations as printable order assets.

## 4. Primary User Journey

1. The user signs in with Google or Facebook.
2. The user creates an album or opens an existing draft.
3. The user selects the album's default print size.
4. The user uploads photos and sees upload and processing progress.
5. The service creates thumbnails, validates print quality, and runs AI assessment.
6. The user arrives at a thumbnail grid. Each ready thumbnail shows its score in the top-right corner and reveals a short assessment on hover, keyboard focus, or mobile tap.
7. The user opens a thumbnail to see a large photo and detailed assessment in a side panel.
8. The user optionally selects photos for guided improvement or short animation generation.
9. The user compares each improved image with the original and accepts or rejects it. Animations remain separate digital assets and never replace the printable image.
10. The user reorders photos, changes individual print sizes, and reviews or adjusts automatic crops.
11. The review page reports blockers such as missing sizes, failed uploads, or low resolution. Skipped, unfinished, or failed AI work does not block printing.
12. The user enters a UK delivery address and reviews GBP prices, delivery, VAT, and the final total.
13. The user pays through hosted checkout and confirms the order.
14. The service creates an immutable order snapshot and queues it for downstream fulfilment.
15. The user sees an order reference and current status, with cancellation available during the configured window before fulfilment begins.

## 5. Functional Requirements

### Authentication and account

- **AUTH-01:** Users can sign in and sign out with Google or Facebook using OAuth/OIDC; the application never handles social account passwords.
- **AUTH-02:** Accounts from different providers may be linked only after verified ownership of both identities.
- **AUTH-03:** Every album, photo, AI result, and order is accessible only to its owner or an authorized administrator.
- **AUTH-04:** Users can request account deletion, subject to any legally required order-record retention.

### Albums

- **ALB-01:** A signed-in user can create, rename, view, and delete a draft album.
- **ALB-02:** Each album has a default print size selected from an administrator-managed product catalog.
- **ALB-03:** Each album enforces a configurable photo limit. The interface shows the used and remaining count before upload.
- **ALB-04:** Album states are `draft`, `submitted`, `in_production`, `completed`, `cancelled`, and `expired`.
- **ALB-05:** Submitted albums cannot be edited. Reordering requires creating a copy or an explicit cancellation workflow.
- **ALB-06:** Concurrent changes cannot silently overwrite one another.

### Photo upload and management

- **PHOTO-01:** Users can select or drag multiple supported image files into a chosen draft album.
- **PHOTO-02:** The service validates actual file type, file size, dimensions, album capacity, and decodability. File extensions alone are not trusted.
- **PHOTO-03:** The initial supported formats should be JPEG, PNG, and HEIC/HEIF if browser and server testing confirms reliable conversion.
- **PHOTO-04:** Each photo shows `uploading`, `processing`, `ready`, or `failed`, with a retry action where safe.
- **PHOTO-05:** The service stores the original privately and generates separate web thumbnails/previews.
- **PHOTO-06:** EXIF orientation is applied before display; sensitive metadata such as GPS coordinates is removed from generated and improved versions.
- **PHOTO-07:** Users can reorder or delete photos while the album is a draft.
- **PHOTO-08:** A photo inherits the album print size unless the user chooses a per-photo override.
- **PHOTO-09:** The review screen warns when resolution is too low for the selected print size and shows the expected crop/aspect ratio.

### AI assessment and improvement

- **AI-01:** AI processing requires clear user consent and identifies the external processor, if one is used.
- **AI-02:** Assessment runs asynchronously and never blocks the rest of the album from loading.
- **AI-03:** A ready assessment contains a documented score, for example 0-100, and no more than three short suggestions.
- **AI-04:** Assessment statuses are `queued`, `processing`, `ready`, `failed`, and `not_requested`.
- **AI-05:** Users can select one or more eligible photos and choose which supported suggestions to apply.
- **AI-06:** Improvement creates a new version; it never overwrites the original.
- **AI-07:** Users can compare original and improved versions and explicitly accept or reject each result.
- **AI-08:** Failed or unsafe AI processing leaves the original available and provides a retry or skip action.
- **AI-09:** AI-generated versions are clearly identified throughout review and order creation.

The scoring rubric and supported improvements must be defined before implementation. Likely assessment dimensions are resolution, exposure, sharpness, noise, composition, and print crop compatibility. Improvements should initially be limited to predictable operations such as exposure, color balance, denoising, sharpening, and crop suggestions.

### Order creation and handoff

- **ORD-01:** Submission validates every selected asset and print option, then shows a final confirmation screen.
- **ORD-02:** Submission is idempotent: retries cannot create duplicate orders.
- **ORD-03:** An order stores an immutable snapshot of photo version, order, print size, quantity, crop settings, and relevant product data.
- **ORD-04:** An accepted order receives a human-readable reference and starts in `pending_fulfilment`.
- **ORD-05:** A transactional outbox or equivalent durable mechanism records the downstream handoff so an order cannot be saved without eventually being sent.
- **ORD-06:** Downstream delivery is retried safely, records attempts, and exposes failures to administrators.
- **ORD-07:** Provider-specific integration is behind a small adapter so the provider can be chosen later.

### Retention and deletion

- **RET-01:** The retention policy is shown before upload and includes the exact expiry date in each album.
- **RET-02:** Retention periods are configurable separately for abandoned drafts, submitted source photos, and generated previews.
- **RET-03:** Users receive a warning before draft photos expire.
- **RET-04:** Expiry removes originals, previews, AI versions, and provider copies where the provider API permits it.
- **RET-05:** Order metadata needed for fulfilment, support, accounting, or legal obligations is retained separately from photo files.
- **RET-06:** Deletion jobs are auditable and retry failures without restoring user access to expired content.

## 6. Recommended Technical Approach

### Architecture

Use a Python-first modular monolith with as few moving parts as possible:

- **Web application:** A currently supported Django release, using Django templates for the first UI.
- **Browser behavior:** HTML and CSS plus a small amount of vanilla JavaScript for uploads, progress, reordering, crop controls, and AI status updates. Avoid a JavaScript framework and frontend build pipeline.
- **Authentication:** `django-allauth` or another maintained OAuth/OIDC integration for Google and Facebook.
- **Database:** PostgreSQL for accounts, albums, photo metadata, AI jobs, and orders.
- **Object storage:** Private S3-compatible storage for originals and generated assets. Do not store large image files in PostgreSQL or on ephemeral web-server disks.
- **Background work:** One worker process, built from the same application image, claims durable jobs from a PostgreSQL table. This avoids Celery and Redis for the expected MVP volume.
- **Image processing:** Pillow with HEIF support, or libvips if memory use becomes a problem.
- **AI integration:** One small server-side OpenAI API module. Add a broader abstraction only if a second provider is actually needed.
- **Administration:** Django admin for catalog values, album limits, retention settings, order status, and failed jobs.

Keep album, media, AI, order, and fulfilment logic in clear Python modules without splitting them into services. Use service functions for business rules so a future REST API and mobile client can reuse them.

### Upload flow

For production, the browser should upload directly to private object storage using short-lived signed URLs:

1. The web application validates album ownership and capacity and creates pending photo records.
2. It returns short-lived, size-limited upload URLs.
3. The browser uploads each file and reports completion.
4. A background task verifies and decodes the stored object before marking it ready.
5. Follow-up tasks create previews and request AI assessment.

This avoids routing large phone photos through the web process. A local-storage adapter can keep development simple.

### Suggested domain model

- **UserIdentity:** user, provider, provider subject ID, verified email.
- **Album:** owner, name, state, default print product, photo limit, expiry date, version.
- **Photo:** album, display order, original asset, selected asset, print-size override, processing state.
- **PhotoAsset:** photo, kind (`original`, `preview`, or `ai_improved`), private object key, checksum, media type, dimensions, created date.
- **Assessment:** asset, state, score, structured suggestions, model/provider version.
- **ImprovementRequest:** source asset, selected operations, state, output asset, accepted date.
- **PrintProduct:** provider code, dimensions, units, aspect ratio, active flag.
- **Order:** owner, album, reference, state, idempotency key, immutable totals/details, submitted date.
- **OrderItem:** order, source asset/checksum, product snapshot, quantity, crop snapshot, display order.
- **OutboxEvent:** event type, order, payload, delivery state, attempt count.

## 7. Security, Privacy, and Reliability

- Use HTTPS, secure cookies, CSRF protection, strict ownership checks, and rate limiting.
- Keep object storage private and serve assets with short-lived signed URLs.
- Encrypt data in transit and at rest; keep secrets in a managed secret store.
- Validate decoded images and set pixel/memory limits to prevent decompression-bomb attacks.
- Scan uploads if required by the hosting or print-provider threat model.
- Do not log signed URLs, image content, OAuth tokens, or unnecessary personal data.
- Document whether AI providers retain uploads or train on them; prefer zero-retention processing terms.
- Make background tasks idempotent and use checksums to detect duplicate delivery.
- Record consent, order transitions, administrative actions, deletion outcomes, and external requests in an audit log.
- Back up database records, test restoration, and avoid retaining expired photos in backups longer than policy allows.

## 8. User Experience and Accessibility

- Design mobile-first and test the complete journey at narrow and wide viewport sizes.
- Keep the primary action obvious on every screen and avoid hidden state changes.
- Use plain language for print quality, AI suggestions, errors, and retention dates.
- Preserve album state after refresh, interrupted uploads, expired sessions, or failed background tasks.
- Support keyboard navigation, visible focus, screen-reader labels, sufficient contrast, and WCAG 2.2 AA targets.
- Never rely on color alone for status or print-quality warnings.
- Give destructive actions a confirmation and explain whether deletion is immediate or queued.

## 9. Initial Configurable Defaults

These are pilot assumptions, not final business decisions:

- Maximum 100 photos per album.
- Maximum 25 MB per original file, with a separate maximum decoded pixel count.
- Draft photo retention of 30 days since last activity, with a warning 7 days before expiry.
- One print copy per photo unless quantities are added to the order flow.
- Up to three AI suggestions per photo.
- Limited retry count with exponential backoff for AI and fulfilment jobs.

Values should live in validated application settings or database configuration, not be scattered through UI code.

## 10. Delivery Plan

### Phase 0: Resolve product decisions and prototype risks

- Choose the first print provider or define the manual fulfilment payload.
- Decide payment, shipping, supported regions, product sizes, crop behavior, quantities, and pricing.
- Choose the AI provider and validate output quality, latency, cost, privacy terms, and failure handling with representative photos.
- Test JPEG, PNG, and HEIC uploads from target phones and browsers.
- Produce low-fidelity screens for the full user journey and test them with a small number of users.

**Exit criteria:** The open decisions in section 13 that affect the MVP are answered, and short technical spikes prove the upload and AI workflows.

### Phase 1: Foundation, authentication, and albums

- Set up Django, PostgreSQL, object storage abstraction, deployment environments, and automated checks.
- Add Google and Facebook sign-in.
- Implement ownership, album lifecycle, print product catalog, and responsive album pages.

**Exit criteria:** A user can sign in and manage only their own draft albums on desktop and mobile.

### Phase 2: Upload and image pipeline

- Implement multi-file uploads, progress, validation, previews, reordering, limits, and print-size inheritance/overrides.
- Add background processing, retries, expiry display, and deletion jobs.

**Exit criteria:** A user can reliably prepare an album of representative phone photos, including recovery from interrupted and invalid uploads.

### Phase 3: AI review and improvement

- Implement consent, queued assessment, scores, suggestions, batch selection, improvement, comparison, and accept/reject.
- Add provider cost, latency, failure, and safety monitoring.

**Exit criteria:** Originals remain intact, every AI state is visible and recoverable, and accepted versions are selected correctly for printing.

### Phase 4: Order submission and fulfilment

- Add final review, validation, idempotent submission, order snapshots, references, outbox delivery, retries, and administration.
- Integrate the selected print, payment, and shipping workflows if they are part of the MVP.

**Exit criteria:** Repeated submission cannot duplicate an order, and every accepted order is either delivered downstream or visibly awaiting retry.

### Phase 5: Pilot and hardening

- Run accessibility, security, privacy, browser, mobile, load, restore, and retention-deletion tests.
- Pilot with a small user group and measure completion, upload failures, AI acceptance, support needs, and fulfilment failures.

**Exit criteria:** No critical defects remain, operational alerts and support procedures exist, and retention has been verified end to end.

## 11. Test Strategy

- **Unit tests:** Album capacity/state rules, print-size inheritance, retention dates, AI transitions, and order snapshot creation.
- **Integration tests:** OAuth callbacks, object storage, background task retries, AI adapters, outbox delivery, and deletion.
- **End-to-end tests:** Sign in, create album, upload on desktop/mobile, accept an AI result, override a size, submit, and recover from failures.
- **Security tests:** Cross-user access, malicious/oversized files, signed URL expiry, CSRF, rate limits, and administrator permissions.
- **Contract tests:** Fulfilment payloads and AI provider responses, including malformed and duplicate responses.
- **Operational tests:** Database restore, queue outage recovery, expired-photo deletion, and idempotent job replay.

## 12. Success Measures

- Percentage of users who submit an order after creating an album.
- Median time from album creation to submission.
- Upload and image-processing failure rates by device, browser, and file format.
- AI assessment completion time, cost per album, and improvement acceptance rate.
- Duplicate-order count, which should remain zero.
- Fulfilment delivery success and retry rates.
- Percentage of expired photo assets deleted within the policy window.
- Accessibility and user-reported ease-of-use issues during the pilot.

## 13. Product Decisions

### Confirmed

- **Market:** United Kingdom only for the MVP, using British English and GBP. Prices shown to consumers include VAT where required. Print dimensions use familiar UK product names, with canonical dimensions stored in millimetres.
- **Payment:** Collect payment immediately before order submission through Stripe Checkout or an equivalent hosted checkout. Do not handle card details directly. Support Strong Customer Authentication, payment webhooks, receipts, refunds, and idempotent retries.
- **Shipping and tax:** Collect and validate the UK delivery address during checkout. Show delivery cost, VAT, and the final total before payment. Receive fulfilment and tracking updates through provider webhooks or scheduled status checks.
- **Initial print range:** Start with popular `6 x 4`, `7 x 5`, `8 x 6`, and `10 x 8` inch prints, glossy and matte finishes, and per-photo quantities. Keep products, prices, aspect ratios, and minimum resolutions configurable in Django admin.
- **Cropping:** Apply a suggested centre crop automatically when the selected print ratio differs. Show the crop before checkout and let the user reposition it, reset it, or revert to the uncropped image and choose another compatible size.
- **Fulfilment access:** Store photos in private object storage, not on a public web server. Send the print provider an order manifest containing short-lived signed download URLs. Use a provider upload API instead if it offers a more reliable private transfer. Never expose permanent public photo URLs.
- **Retention:** Make retention periods configurable by asset and album state. Show exact expiry dates and warn users before deletion.
- **AI provider:** Use OpenAI models through the server-side API for assessment, supported improvements, and animation generation. Keep API credentials on the server and record the model/version used for each result.
- **AI participation:** Start assessment by default after upload, but provide a clear skip option before processing and allow users to continue without AI. AI failure must never block printing an otherwise valid original.
- **Sensitive content:** Apply explicit consent, age-appropriate safeguards, provider policy checks, and restricted administrator access for photos containing faces, children, or sensitive content. Reject prohibited content and provide a clear user-facing reason and review path where appropriate.
- **Order changes:** Permit cancellation only within a configurable time window and only before fulfilment starts. Refund through the original payment method. Submitted albums remain immutable; a replacement order starts from a copied album.
- **Administration:** Begin with Django admin for user/account support, account suspension, album and order management, catalog and retention configuration, failed-job retry, cancellation/refund recording, and audit-log review. Photo content is hidden from administrators by default and accessed only when support duties require it.
- **Engineering priority:** Simplicity takes precedence over speculative flexibility. Use one codebase, one application image, managed services, and the fewest operational components that satisfy security and reliability requirements.

### Values to finalize during Phase 0

These do not change the chosen direction, but exact values or external contracts are still required:

1. Select the first UK print provider and confirm its product codes, file specifications, transfer method, order statuses, service levels, and webhook contract.
2. Set prices, delivery charges, free-delivery thresholds, minimum resolutions, maximum quantities, and the precise cancellation/refund window.
3. Set retention durations for draft, submitted, completed, cancelled, improved, and animated assets.
4. Define the AI scoring rubric, supported improvement controls, animation styles/duration/output format, and content-review escalation rules.
5. Confirm the public privacy notice, terms, consent wording, refund policy, support contact, and data-processing agreements before accepting real customer photos.