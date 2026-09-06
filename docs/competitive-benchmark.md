# UK Competitive Benchmark and UI Direction

Reviewed: 6 September 2026.
Application baseline: `3d32c7d`; implemented scope is described in
[README.md](../README.md). This is a comparison and proposed direction, not an
instruction to implement deferred work in [plan.md](../plan.md).

## Recommendation

Aim for the clarity of an established print service and the visual coherence of
a modern photo app, with a distinct emphasis on informed print approval.
Do not compete by reproducing a large gift catalogue or adding more decoration.

The current UI is a cleaner foundation than the original design, but it is not
yet competitive as an end-to-end printing experience. Users can manage album
metadata, not upload, review crops, buy prints or track delivery. Attractive
sign-in and empty-album screens cannot establish parity with working editors.

Working signature: **BPM Print Proof**. This is a proposed interaction concept,
not a uniqueness or trademark claim: the customer can understand exactly which
version and crop will be printed, what it costs, and what happens to the files.

## Evidence and Limits

- Representative established UK-serving competitors: CEWE, Photobox, Snapfish
  and FreePrints. Popsa is included as an additional modern UI/automation
  benchmark. This is not a market-share ranking or an exhaustive market survey.
- Official product/help pages were read on the review date. Feature descriptions
  below are supplier claims unless identified as directly observed.
- Photobox's print page was inspected in a browser at 1440px and 390px. Its
  desktop product imagery/navigation and a mobile newsletter overlay were
  directly observed. Popsa's public print page was also visually inspected.
- CEWE's browser view remained covered by its consent interface in this session;
  its feature comparison is based on official page content, not a complete
  unobstructed visual audit. This is not evidence of a universal website defect.
- No competitor account was created, no photos were uploaded, no native app was
  installed and no order was placed. Editing quality, full checkout usability,
  delivery performance, print accuracy and accessibility parity are unverified.
- Our desktop/mobile observations come from the implementation's prior browser
  checks at 1440px, 390px and 320px, not a matched competitor usability study.
- Promotions, product ranges and prices can change. Do not compare headline
  per-print prices without matching quantity, finish, postage and eligibility.

## Competitor Comparison

| Service | Evidence from official pages | What to learn | Gap against our current implementation |
| --- | --- | --- | --- |
| [CEWE](https://www.cewe.co.uk/photo-printing.html) | Print styles and photographic paper information; online, desktop-software and app creation options; price/delivery information; satisfaction guarantee and customer support. | Explain the physical product and provide visible purchase reassurance. | No print-material selection, orderable product, delivery promise, support workflow or tested fulfilment. |
| [Photobox](https://www.photobox.co.uk/photo-printing) | Premium/large/retro print choices; matte/gloss and borders; crop tools and filters; browser/mobile creation; bulk-price information. Browser observation: recognisable teal identity, real prints in context, direct creation CTA, visible account/basket/support. | Product clarity and a recognisable design system, not just an attractive generic login. | No real photo gallery, crop editor, finish/border/quantity workflow or price summary. |
| [Snapfish](https://www.snapfish.co.uk/photo-printing) | Broad print range, matte/gloss options and advertised AI auto-enhancement. Its [new-features page](https://www.snapfish.co.uk/whats-new) describes phone-to-desktop upload using a QR code. | Reduce transfer friction and make batch preparation efficient. | No uploads, cross-device transfer, bulk editing or enhancement yet. QR transfer would be additional scope, not an MVP requirement by default. |
| [FreePrints](https://www.freeprintsapp.co.uk/) | App-led photo selection, quantity selection, cropping and delivery. Advertises up to 45 free 6x4 prints per month, up to 500 per year, with conditions and delivery charges. | A narrow, understandable repeat-order task and explicit offer conditions. | No phone-photo-to-order workflow or comparable total price. Native app ease has not been tested. |
| [Popsa](https://popsa.com/en-gb/) | Advertises automatic layouts, print-quality scores, generated captions, cancellation and account-data deletion. Its [prints page](https://popsa.com/en-gb/products/photo-prints/) lists crop/border/caption options and says colour enhancement must be performed before upload. | Coherent product presentation, reduced decision effort and visible confidence checks. | No quality assessment, comparison workflow or customer-facing data-deletion flow. Features advertised for the wider platform must not all be assumed to apply to loose prints. |

Important corrections to positioning:

- **AI enhancement is not unique:** Snapfish already advertises it.
- **Print-quality scores are not unique:** Popsa advertises a score out of ten.
- **Privacy controls are not unique:** Popsa explicitly advertises data deletion;
  this review does not establish weaker privacy at the other services.
- **Browser ordering is not unique:** CEWE and Photobox both offer it. Avoiding an
  app installation may be useful relative to an app-led offer, not the whole market.

## Where We Have Strengths Today

1. **A focused workspace.** Album pages have a short action set and no promotional
   cross-selling or newsletter interruptions. Photobox's mobile newsletter overlay
   was observed during this review. This is a design advantage to preserve, not
   proof that our unfinished workflow is faster than its editor.
2. **Consistent responsive components.** Shared forms, local fonts/icons, visible
   focus states and 44px icon controls have been checked on narrow screens.
   Sampled automated accessibility checks passed after contrast fixes. This does
   not establish complete WCAG compliance or superiority over competitors.
3. **A sound ownership foundation.** Owner-scoped album operations, read-only
   submitted/expired states and explicit version checks are implemented and
   tested. These are valuable engineering foundations, not unique selling points.
4. **Visible album expiry.** The UI shows an exact date, which can support a clear
   retention experience later. Automatic deletion, warnings and external-copy
   cleanup are not implemented, so no deletion guarantee should be marketed yet.

There is currently no evidence to claim better print quality, AI accuracy,
checkout conversion, delivery, pricing or overall ease of use.

## UI Gaps to Address

| Priority | Current gap | Proposed response |
| --- | --- | --- |
| Next design step | Book-shaped covers imply a bound photo-book product, while the MVP sells loose prints. | Use print stacks/contact sheets for the album metaphor. Once uploads exist, show the user's actual photos; never substitute decorative stock images for album content. |
| Next design step | Generic scenery and a small brand mark do not establish a distinctive print service. | Build a consistent print-edge/crop-corner motif and commission or license relevant physical-print imagery. Keep the primary application usable rather than adding a marketing landing page. |
| Next design step | Entry is a development login with no product or purchase context. | Design the future entry, print selection and signed-in return states together. Show useful product context without requiring an account merely to read it. Moving sign-in later or allowing guest uploads requires an explicit change to the current journey and ownership design. |
| Upload milestone | No meaningful working-gallery states. | Design ready, uploading, retry, failed, empty and expired states with real-photo layouts; batch selection and a clear processing summary. |
| Print-review milestone | No preview of the actual output. | Show selected dimensions, crop boundary, border/finish and quantity together; make per-photo overrides and reset clear. A small change must not unexpectedly reset other choices. |
| Print-review milestone | No easy way to understand image changes. | Compare original versus proposed result with an explicit selection. Explain print-readiness for the chosen size and crop, not the aesthetic worth of a family photo. |
| Checkout milestone | No running total or delivery certainty. | Show a persistent summary of quantities, prices, delivery, applicable VAT and final total before payment, with unavailable details clearly labelled rather than guessed. |
| Before pilot | No complete trust/recovery experience. | Implement clear help, policies, order status, cancellation eligibility and retention actions. Do not display invented reviews, guarantees or delivery dates. |

Small supporting text also needs a readability review with actual users. Minimal
layouts should not become low-contrast or undersized interfaces in pursuit of style.

## Proposed Signature: BPM Print Proof

### Visual Language

- Keep the existing DM Sans typography, neutral surfaces, charcoal actions and
  restrained coral accent. Let customer photos supply most of the colour.
- Use a small, consistent crop-corner/print-edge detail in the brand, selection
  state and print preview. It should identify BPM without competing with photos.
- Use light paper depth for actual print previews, not decorative nested cards.
- Reserve expressive photography for entry/product context; keep repeated work
  screens dense enough for selecting and comparing many photos.
- Use the same spacing, status vocabulary and icon treatment in gallery, viewer,
  review, checkout and order status. Respect reduced motion and keyboard use.

### Distinctive Interaction

A proposed print-proof view should answer five questions in one place:

1. **Which image?** Original or explicitly accepted improved version.
2. **What will be cut off?** Accurate crop and a visible reset/adjust action.
3. **Will it print well at this size?** Explain specific resolution or image
   issues with uncertainty; do not promise exact screen-to-paper colour matching.
4. **What am I buying?** Size, finish, quantity and cost; delivery in order review.
5. **What happens to my files?** Actual expiry and applicable AI-processing choice.

On desktop, place the photograph beside compact controls. On mobile, retain the
same information order with reachable controls and a summary that does not cover
the photograph or keyboard. Batch changes need a clear selection count and an
easy recovery path. These are proposed designs, not currently available controls.

The positioning hypothesis is that **clear, reversible print approval** will be
more valuable than another opaque AI score. It needs testing; the existence of
similar features elsewhere is not ruled out by this research.

## What "At Least as Good" Should Mean

Use a matched task, not a comparison between our login and competitors' storefronts:
prepare 20 consented test photos, mix portrait/landscape images, include a low
resolution image, set quantities, correct a crop, leave and resume, then identify
the delivered total before payment. Test native apps separately from browsers.

Proposed acceptance gates, not measured results:

- At least 4 of 5 initial target users finish the available preparation task
  without assistance; follow with a larger study before claiming superiority.
- Users can identify the selected version, crop and final total correctly.
- Measure task success, active task time, crop mistakes, abandoned attempts and
  perceived trust against two matched competitors. Comparable task success and
  no worse median active time are the initial parity goal; a tiny pilot is not
  statistical proof of equivalence.
- Validate at 320, 390, 768 and 1440px, with 200% zoom, keyboard-only operation
  and VoiceOver or TalkBack. No horizontal overflow or obscured controls.
- Target WCAG 2.2 AA across the full flow, including errors and dialogs. Automated
  checks supplement, rather than replace, manual assistive-technology testing.
- Aim for mobile Core Web Vitals at the 75th percentile of LCP <= 2.5s,
  INP <= 200ms and CLS <= 0.1 once field data exists. Local preview checks do not
  establish these results; report photo-upload time separately by connection.
- Verify interrupted uploads, refresh/session recovery, stale edits and duplicate
  submissions without losing customer work. Previously reviewed SQLite contention
  and unavailable-provider errors remain separate fixes before a public pilot.

## Recommended Next Work

1. Agree the loose-print visual metaphor and Print Proof concept. Produce a
   clickable desktop/mobile prototype of gallery, crop review and final summary,
   using clearly labelled synthetic fixtures, not fake functioning controls.
2. Test that prototype with a small group against the matched competitor task.
   Refine terminology and information hierarchy before another cosmetic redesign.
3. Implement the upload/gallery milestone with those states and acceptance tests.
4. Integrate pricing, payment and fulfilment only after their contracts are agreed.

Do not add native apps, facial recognition, a broad gift catalogue, QR transfers
or more AI features solely because a competitor has them. They are separate scope
decisions. Keep the current Django/template architecture unless evidence shows it
cannot meet the experience requirements.