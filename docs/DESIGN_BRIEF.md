# Design Brief — Ops-Grade UI Conventions (Session D reference)

Distilled from best-in-class B2B ops tools (Linear, Stripe Dashboard, Vercel,
Retool) and healthcare queue tools (CoverMyMeds, Availity). Session C applied
most of the foundation; this brief guides the Session D polish pass.

## 1. Operational queue tables

- **Row height:** 40–44px (`py-2.5`/`py-3` at 13px text). Dense but scannable.
  Linear uses ~38px; Stripe ~44px. Never taller for queue rows.
- **Case identity at a glance:** an ops row must answer "who / what / where /
  how long" without clicking: patient name, drug, status, case age. IDs are
  secondary (mono, muted, truncated to 8 chars). *Requires backend join —
  planned Session D API change.*
- **Column alignment:** text left; numbers right; never center. Age/date
  columns right-most, muted (`text-slate-400 text-[12px]`).
- **Status badges:** subtle-fill + ring convention (already in StatusBadge):
  `bg-*-50 text-*-600/700 ring-1 ring-inset ring-*-200`, 11px medium. Solid
  fills read as buttons — avoid.
- **Priority:** words not numbers (High/Med/Low — done, PriorityBadge). Reserve
  red for High only.
- **Hover:** whole-row `hover:bg-slate-50/50` + `cursor-pointer` when row
  navigates. The whole row should be the click target, not just the ID link.

## 2. "AI-generated" tells → professional replacements

| Tell | Replacement |
|---|---|
| Gradient hero banners, floating blurred orbs | Dense utility panel (done: Needs Attention) |
| Emoji as icons | Icon set, one weight (done: lucide) |
| Two accent colors across pages | One accent + semantic colors only (done) |
| `window.location.reload()` after mutations | Refetch state (done) |
| Marketing copy inside the app ("let AI handle it") | Task-oriented microcopy |
| Fake chrome (dead search/bell, "Online" badge) | Only render what works (done) |
| Uniform `space-y-6` everywhere | Group related, separate unrelated |

## 3. Loading / empty / error states

- **Loading:** skeleton rows (shimmering `bg-slate-100` bars matching column
  layout) beat spinners for tables — no layout shift. Spinner acceptable for
  full-page first load only. *Session D: swap table Spinners for skeletons.*
- **Empty:** icon + one-line title + one-line hint + primary action (done).
  Never render an empty state while an error exists (done — separate states).
- **Error:** inline banner at content top, keep stale data visible if any,
  always offer Retry (done — ErrorBanner).

## 4. Toolbar / filter / refresh patterns

- Filter chips: single row, active = solid accent, inactive = white + border
  (done). >8 statuses → overflow into a "More" dropdown rather than wrapping.
- **Search:** debounce 250–300ms, cancel in-flight requests (patients page
  currently fires per keystroke — Session D).
- **Pagination:** cursor or offset with explicit "Load more" / page controls;
  never a silent `limit: 50` (Session D).
- **Polling:** ops queues auto-refresh every 30–60s with a subtle "Updated 12s
  ago" indicator; pause when tab hidden (`document.visibilityState`). Statuses
  changing constantly is the premise of this product (Session D).

## 5. Color discipline

- One brand accent (teal) for interactive elements only: links, primary
  buttons, active nav, focus rings.
- Semantic status palette, used consistently: green/teal = success-terminal,
  red = failure/destructive, amber = waiting-on-human, blue/indigo = system
  in-progress, slate = neutral/terminal-inert.
- Background layering: page `#fafbfc` → card `white` + `border-slate-200/80`
  → nested emphasis `bg-slate-50/50`. Never stack two same-level surfaces.

## 6. Destructive confirmations

- Modal confirm for irreversible/high-impact (Cancel PA — done).
- Type-to-confirm only for catastrophic (delete account/data) — not needed here.
- Button in dialog names the action ("Cancel PA", not "OK") (done).
- Post-action: refetch + toast/inline feedback, never full page reload (done).

## 7. Healthcare-specific conventions

- **Patient identification:** always `Last, First` + DOB together (two-factor
  ID is standard in clinical UIs to prevent wrong-patient errors). Apply when
  patient columns land in the queue (Session D).
- **Case age / SLA:** relative age (`3h`, `2d`) with escalating color as SLA
  approaches: neutral → amber (>24h) → red (>72h). Age formatter exists;
  add thresholds in Session D.
- **PHI discipline:** no PHI in URLs, page titles, or toasts; mask member IDs
  to last-4 in list views (`•••• 1234`); full detail only on the case page.
- **Audit affordance:** every state-changing action visible in a timeline
  (done — agent timeline on PA detail).

## Session D checklist (from this brief)

- [ ] Skeleton loaders for tables (replace Spinner-in-table)
- [ ] Patient (`Last, First` + DOB) and drug columns in queue (backend join)
- [ ] Debounced patient search with request cancellation
- [ ] Pagination controls (queue + patients)
- [ ] 30–60s polling with "Updated Xs ago" + visibility pause
- [ ] SLA color thresholds on case age
- [ ] Member ID masking in list views
- [ ] a11y: aria-labels on icon buttons, focus traps in dialog, WCAG AA
      contrast for 11–12px muted text (bump `slate-400` → `slate-500` on white)
