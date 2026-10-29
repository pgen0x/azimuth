# Azimuth dashboard — design direction

Source: the product owner's answers (2026-10-29), transcribed. This file is direction, not code.

## Identity

- **Product:** a local, read-only operational dashboard for one Solana DLMM liquidity bot. Audience: its single operator,
  checking capital, daily results and where SOL went, often for long stretches and at night.
- **Personality: precision instrument.** Calm, serious, data-dense, like a measuring tool or a professional terminal.
  The accent is reserved for the numbers that matter. Nothing performs; everything reports.
- **Name / mark:** text wordmark "azimuth" plus a simple geometric compass/bearing SVG icon (also the favicon).
  No photos, no avatars, no illustrations of people.

## Theme

- **Dark only.** No light mode, no toggle.
- **"grid2 modern" = both:**
  1. **Modular panel grid:** every panel sits on a strict 12-column grid with thin dividers between panels, like a trading
     desk layout.
  2. **Fine grid-line motif in the background** that lines up with (continues) the panel dividers.
  Purpose (R-07): the grid is the identity motif. It expresses "measured, on a bearing", and the background lines must
  align with the panel structure so the motif reads as the instrument's graticule, not decoration.

## Palette

- Dark neutral base (near-black background, slightly lifted panel surface, hairline dividers).
- **One accent: amber / burnished copper.** Warm, contrasts with the green/red data, evokes a compass needle. Used
  sparingly: the focal number on a screen, the active tab, focus rings, the current-day marker.
- **Data colors:** profit green and loss red, chosen to stay accessible (WCAG AA on the dark surface, and never color
  alone: sign and label always shown). Neutral grey for zero/unmeasured.
- Unmeasured / unknown is its own visual state (never drawn as zero).

## Typography

- **One technical sans-serif for all UI**, with **tabular figures** for every number so columns align.
- No monospace headings, no wide-tracked uppercase labels.
- Fonts must work offline (self-hosted or system stack); the dashboard is loopback-only.

## Charts (requested, in the style of an LP tracker report)

1. **Daily balance line:** `cash` and `known` (SOL) per day in the viewer's local time zone.
2. **Daily PnL bars:** Δcash per day, green/red.
3. **Calendar chart:** month calendar heatmap of daily PnL (like metlex.io), green/red intensity, unmeasured days distinct.
4. **NAV bridge waterfall:** LP realized → fees → rent → swap residual → token marks → unrealized → external → unexplained,
   showing where SOL went.
5. **Realized per mode:** stacked daily bars by mode (pulse / turnover) plus cumulative line.

All chart values come from the collector's real data; empty, loading and error states are required.

## Access

- **Password login screen** before any data is shown.
- Password hash supplied via an environment variable set in a systemd drop-in env file; the server never stores or logs
  the plain password. Still loopback-only.

## Dials

Dial: ENERGY 1 / RHYTHM 2 / MOTION 1
(calm instrument; panel grid is consistent with a few deliberate breaks for the focal chart; hover/focus states and chart
tooltips only, no decorative animation)

## Time

Public repo, international users: store and transmit time in UTC (epoch / ISO-8601 with offset). Day boundaries for daily
charts are computed in the viewer's local IANA time zone (sent by the browser), defaulting to UTC. Every displayed time
shows its zone. No hard-coded regional time zone.
