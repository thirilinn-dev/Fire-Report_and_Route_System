# Demo validation status — 2026-10-07

The emergency console is running at http://127.0.0.1:8000/emergency/.

Implemented: four roles, citizen registration, phone/legacy login, station-scoped
account management, rank, duty/leave, timed acting managers, individual vehicles,
jurisdiction/level response plans, preview and administrator-confirmed reservation,
additional dispatch waves, actual staff participation and substitutions, status
updates, station/final reports, review and closure, notifications with separate
read/acceptance states, audience-scoped posts, filters, pagination, public map
privacy, local Dijkstra routing, and Myanmar/Latin PDFs.

## Verified

- Fresh MySQL test database: **82 tests passed** in 93.131 seconds. Command:
  `python -B manage.py test --noinput`, run from `fire_route_system`.
- Concurrent independent MySQL connections cannot reserve the same vehicle or
  select the same employee for two incidents. These tests require MySQL.
- Permission and station boundaries, active session revocation, CSRF, registration,
  coordinate validation, duty overlap, leave, acting periods, shortages, escalation,
  downgrade retention, resource return, actual resources, report revision,
  closure, post audiences/drafts, privacy, filters, and pagination were checked.
- Migration consistency, Django system checks, and `git diff --check` pass.
  `pipenv verify` confirms the lock file matches the manifest.
- OSM import: **199,503 nodes and 423,734 directed road edges**. All 22 active
  stations inside the demo's Mandalay bounds produced routes to the test location
  21.975, 96.083. Route calculations took approximately 3–4 seconds each.
- Browser checks covered all four role dashboards and the complete incident 30
  workflow: Citizen report → Admin confirmation/dispatch → Station Admin selects
  on-duty personnel → departure/arrival/update/return → station report → lead
  final submission → Admin approval/closure. The recorded actual resources are
  two vehicles, one firefighter, and 250 gallons. OSM map tiles render normally.
- PDF raster inspection confirms Myanmar, Latin text, digits, and the route
  diagram render. PyMuPDF recovered the logical Myanmar title from `ActualText`.
  The font is embedded and licenses/rebuild instructions are included.
- Seeder reruns preserve existing account passwords and response plans.

## Demo data and practical limits

Station names and response quantities are illustrative and need local review.
Existing station records include duplicate names and one active station coordinate
outside the Mandalay demo area. The import warns about that coordinate; routing
shows a clear error until an administrator corrects it. Existing records were
preserved. Distances follow OSM roads and one-way access; graph endpoint connector
distances are shown separately. This demo does not model traffic or live vehicle
locations. Map tiles and initial road downloads need network access.

PDF copy/search support can differ across readers; the logical Unicode is included
in standard ActualText metadata. No Chat, SMS, OTP, or live vehicle tracking is
included, as agreed.

## Original FireRoute UI restoration

The emergency pages now reuse the original CAD sidebar, branding, topbar, theme
controls, and login page. Dashboard cards and the station map layout use the
original styling while retaining the emergency workflows. Twenty focused page,
login, dashboard, map, and privacy tests passed. Browser checks covered the
requirements page, light/dark appearance, and station search/map selection.

## Local artifacts

Ignored `runtime/` contains the road export, route-validation JSON, test logs,
`demo-browser.png`, and `demo-incident-30.pdf`. The configured laptop MySQL database
continues to hold existing records and the clearly labelled browser demo incident.

The local `.env` and validation artifacts are ignored by Git. Git publishing is performed only on an explicit user request.
