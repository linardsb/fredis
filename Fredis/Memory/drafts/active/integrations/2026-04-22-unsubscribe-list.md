# Gmail Unsubscribe Candidates — 2026-04-22

**Context:** 201 unread in inbox, almost all marketing / newsletter residue. Below is a triaged kill-list from the top of the backlog. Open each, scroll to the footer, click Unsubscribe. Gmail's built-in "Unsubscribe" link next to the sender name also works for most.

## Tier 1 — Kill immediately (aggressive senders, low/no value)

| Sender | From address | Why |
|---|---|---|
| Jason Wardrop | `jason@m.jasonwardrop.com` | Multi-email/day sales sequence ("last chance", "you deserve a win", "what if this is just another thing?"). Classic marketing funnel. |
| Patrick Bailouni / Trading Mindset | `Pat@patbailouni.com` | Cold-sequence trading course marketing. |
| AlphaInfuse | `support@alphainfuse.com` | Hair transplant product marketing. |
| Car Finance 247 | `CarFinance247@info.carfinance247.co.uk` | Car finance promo — only relevant if actively buying. |
| CarGurus | `cargurus@em.cargurus.co.uk` | Saved-search price alerts — kill unless still car-shopping. |
| zichain.io | `info@zichain.io` | Crypto-adjacent cold outreach. |

## Tier 2 — Kill unless you actively use them

| Sender | From address | Why kill / why keep |
|---|---|---|
| Lumosity | `newsletter@notifications.lumosity.com` | Brain-training promos + discount nudges. Keep only if you're still using the app. |
| Indeed job alerts | `donotreply@jobalert.indeed.com` | Daily "jobs in East Grinstead" digest — kill unless actively job-hunting. |
| LinkedIn notifications | `notifications-noreply@linkedin.com`, `messages-noreply@linkedin.com`, `groups-noreply@linkedin.com` | Search-appearance pings, group digests, "follow this person" recs. Turn off most notification categories inside LinkedIn Settings → Communications → Email rather than per-mail unsubscribe. |
| Every | `hello@every.to` | Paid tech newsletter — keep only if you're reading it. |
| Indie Hackers | `channing@indiehackers.com` | Founder digest — useful but noisy. Kill or move to a "Read Later" filter. |

## Tier 3 — Do NOT unsubscribe (operational / identity)

| Sender | Why keep |
|---|---|
| `wordpress@neutrigy.com` | Your WordPress site's operational alerts (plugin updates, security). |
| `security-noreply@linkedin.com` | Account security — password resets, new-device logins. |
| `analaura.suarez@gmail.com` | Personal contact (not marketing). |

## One-pass cleanup plan

1. Open Gmail → search bar → paste each address below, hit Enter, click "Unsubscribe" at the top of any message, then delete the thread:
   ```
   from:jason@m.jasonwardrop.com
   from:Pat@patbailouni.com
   from:alphainfuse.com
   from:carfinance247.co.uk
   from:em.cargurus.co.uk
   from:zichain.io
   ```
2. LinkedIn notifications — do it inside LinkedIn, not per-email: Settings → Communications → Email → turn off Recommendations, Groups, Network activity. Leave Security + direct messages on.
3. Indeed — log in, Settings → Job alerts → pause or delete the "East Grinstead / html-css" alert.
4. Indeed + LinkedIn aside, once Tier 1 is done, re-run `gmail unread` — you'll likely halve the count.

## Optional follow-ups

- **Filter, don't delete:** if you want to keep Every / Indie Hackers but out of inbox, create a Gmail filter → apply label "Read Later" → skip inbox.
- **Mass-archive old unread:** 23+ of the unread items are from **2021** (Ana Laura Suarez, old school/scout threads). Consider `is:unread older_than:2y` → Select all → Mark as read. Nothing in them is actionable now.
- **Never-unsubscribe list worth noting:** WordPress site alerts, LinkedIn Security, banking/HMRC, anything from `@gov.uk`, calendar invites, 2FA senders.

---

**Advisor note:** I have not sent or clicked anything. All unsubscribe actions need to happen in your Gmail UI — one-click Unsubscribe buttons are safer than clicking footer links inside the email bodies (which can be tracked).
