# AquaTrack — Species Environmental Behavior Dataset

This file is the editorial dataset behind the species detail pages and the "environmental
triggers" panels on the site. It is human-readable first and machine-readable second: every
entry answers the same practical question a fisherman asks on the water —
*"given what the sky and sea are doing right now, is this fish likely in front of me?"*

Each species entry records:

- **Natural range** — the lat/lng box where the species is realistically expected around the
  Maharashtra west coast, so the map and database can flag out-of-range sightings.
- **Preferred environment** — the numeric ranges the prediction model already uses
  (temperature, depth, current). These are kept in sync with `backend/app/data/species_db.py`.
- **When it rains** — how the species responds to rain and runoff.
- **When a storm hits** — storm tolerance and the short-term behavior during rough weather.
- **When it is hot** — behavior above the preferred temperature band.
- **When it is cold** — behavior below the preferred temperature band.
- **Tide affinity** — how strongly the species is driven by tide changes.
- **Night activity** — whether the species is still worth looking for after dark.
- **Surface-feeding behavior** — whether the species feeds on or near the surface, which
    matters a lot for where and how you target it.

---

## How to read a trigger row

A trigger row is not a guarantee. It is a *directional hint*:

- **Move offshore** — the fish is likely leaving the near-shore zone after this trigger.
- **Move shallow** — the fish is likely pushing into shallower water.
- **Feed** — conditions are good enough that active feeding becomes likely.
- **Shut down / scatter** — feeding drops and the fish become harder to target.
- **Hold / no strong change** — the trigger does not strongly move the species on its own.

These short labels are editorial condensation. The full text for each species lives in the
species_db fields `monsoon_peak`, `monsoon_off`, `prefers_rain`, `storm_tolerance`,
`hot_behavior`, `cold_behavior`, `tide_affinity`, `night_activity`, and
`surface_feed_behavior`.

---

## Species

### 1. Indian Mackerel — *Rastrelliger kanagurta*

- Preferred temperature: **22–28°C**
- Preferred depth: **20–100 m**
- Preferred current: **0.2–0.8 m/s**
- Typical habitat: **Coastal / Continental Shelf**
- Conservation status: **least_concern**
- Legal catch status: **regulated**
- Natural range box: **14.0°–21.0° N, 68.0°–75.5° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Post-monsoon (Oct–Dec): strongest near-shore feeding runs. |
| Monsoon off-season | Pre-monsoon (Mar–May): warm, clear water, active surface feeders. |
| Rain | Prefers rain-linked productivity; near-shore feeding often improves with runoff-driven bait. |
| Storm | Moderate — schools scatter in heavy chop, regroup after the front passes. |
| Hot | Above 30°C moves slightly deeper and slows surface feeding. |
| Cold | Below 21°C activity drops; schools compress toward warmer shelf water. |
| Tide | Active on rising tide and tide changes near shore. |
| Night | Moderate — schools stay near surface at night in calm weather. |
| Surface feeding | Strong — readily feeds on the surface when bait is present. |

---

### 2. Sardine — *Sardinella longiceps*

- Preferred temperature: **23–30°C**
- Preferred depth: **10–80 m**
- Preferred current: **0.1–0.6 m/s**
- Typical habitat: **Coastal / Pelagic**
- Conservation status: **least_concern**
- Legal catch status: **regulated**
- Natural range box: **12.0°–20.5° N, 68.0°–74.5° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Southwest monsoon onset (Jun–Jul): plankton bloom drives nearshore abundance. |
| Monsoon off-season | Winter (Dec–Feb): still present but more dispersed. |
| Rain | Prefers rain-associated plankton pulses; abundance often tracks productive coastal water. |
| Storm | High in shoals — tolerates rough surface water; avoids the strongest breakers. |
| Hot | Tolerates warm water well; blooms during hot months. |
| Cold | Below 22°C shoals thin out and drift offshore deeper. |
| Tide | Loose — more driven by plankton drift than tide. |
| Night | Low to moderate — mostly daylight shoaling. |
| Surface feeding | Moderate — filter-feeder; surface only when baitfish are present. |

---

### 3. Shrimp (Penaeid) — *Penaeus spp.*

- Preferred temperature: **24–31°C**
- Preferred depth: **5–60 m**
- Preferred current: **0.05–0.4 m/s**
- Typical habitat: **Inshore / Estuarine / Muddy bottom**
- Conservation status: **least_concern**
- Legal catch status: **regulated**
- Natural range box: **13.0°–20.5° N, 68.5°–74.0° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Southwest monsoon (Jun–Sep): estuarine flushing and productivity peak. |
| Monsoon off-season | Winter (Nov–Feb): still active near river mouths and sheltered bays. |
| Rain | Prefers rain — estuarine flushing and nutrient input are productive for penaeids. |
| Storm | High in sheltered water; avoids open-bay chop during storms. |
| Hot | Warm water suits growth; extreme heat spikes can push them deeper in the water column. |
| Cold | Below 23°C activity slows; estuary-fed grounds remain best. |
| Tide | Strong — moving tides concentrate shrimp in channels and edges. |
| Night | High — many penaeid species move up in the water column at night. |
| Surface feeding | Low — bottom and mid-water feeder, not a surface species. |

---

### 4. Kingfish — *Scomberomorus guttatus*

- Preferred temperature: **22–29°C**
- Preferred depth: **10–120 m**
- Preferred current: **0.2–0.9 m/s**
- Typical habitat: **Coastal / Shelf edge**
- Conservation status: **near_threatened**
- Legal catch status: **regulated**
- Natural range box: **12.0°–21.0° N, 68.0°–75.0° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Pre-monsoon and post-monsoon — strong feeding runs along the coast. |
| Monsoon off-season | Mid-monsoon: may move farther offshore or hold on current edges. |
| Rain | Not strongly rain-driven; does better where rain-driven runoff meets clear coastal water and bait. |
| Storm | Moderate — avoids the worst surface storm chop; holds deeper or on edges. |
| Hot | Above 28°C may shift slightly deeper and hunt current edges. |
| Cold | Below 21°C feeding slows and aggregations loosen. |
| Tide | Moderate — often near structure and current changes at tide turns. |
| Night | Moderate to high — predator that can feed after dark in clear water. |
| Surface feeding | Strong — explosive surface strikes when chasing bait. |

---

### 5. Anchovy — *Stolephorus spp.*

- Preferred temperature: **22–30°C**
- Preferred depth: **5–50 m**
- Preferred current: **0.05–0.5 m/s**
- Typical habitat: **Coastal / Pelagic**
- Conservation status: **least_concern**
- Legal catch status: **unrestricted**
- Natural range box: **12.0°–20.5° N, 68.0°–74.5° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Southwest monsoon and post-monsoon — plankton-driven abundance peaks. |
| Monsoon off-season | Winter: still present but scattered near productive zones. |
| Rain | Prefers rain-associated productivity; often abundant where plankton blooms. |
| Storm | High in large, tight shoals; dispersed by extreme surface turbulence. |
| Hot | Tolerates warm water; blooms during hot productive months. |
| Cold | Below 21°C shoals thin out near shore. |
| Tide | Weak — more driven by plankton and currents than tide. |
| Night | Low to moderate — mostly daytime schooling. |
| Surface feeding | Moderate — surface and mid-water filter-feeder. |

---

### 6. Silver Pomfret — *Pampus argenteus*

- Preferred temperature: **22–28°C**
- Preferred depth: **30–100 m**
- Preferred current: **0.15–0.6 m/s**
- Typical habitat: **Shelf / Soft bottom**
- Conservation status: **vulnerable**
- Legal catch status: **restricted**
- Natural range box: **12.0°–21.0° N, 68.0°–75.0° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Post-monsoon to winter — common in market landings. |
| Monsoon off-season | Mid-monsoon: availability patchy; often holds on cleaner shelf water. |
| Rain | Not strongly rain-driven; prefers cleaner shelf/soft-bottom water. |
| Storm | Moderate — holds slightly deeper in heavy weather. |
| Hot | Above 28°C may shift to deeper shelf water. |
| Cold | Below 21°C feeding activity declines. |
| Tide | Moderate — often near soft-bottom edges and current changes. |
| Night | Low to moderate — more of a daytime/evening feeder. |
| Surface feeding | Low to moderate — mid-water and bottom feeder. |

---

### 7. Tuna (Skipjack) — *Katsuwonus pelamis*

- Preferred temperature: **18–30°C**
- Preferred depth: **10–250 m**
- Preferred current: **0.3–1.2 m/s**
- Typical habitat: **Offshore / Pelagic**
- Conservation status: **least_concern**
- Legal catch status: **regulated**
- Natural range box: **10.0°–22.0° N, 65.0°–78.0° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Southwest monsoon: offshore current fronts and upwelling attract schools. |
| Monsoon off-season | Post-monsoon: still present offshore on current edges. |
| Rain | Not near-shore rain-driven; responds more to offshore current and temperature fronts. |
| Storm | High — pelagic and offshore; tolerates rough open water. |
| Hot | Tolerates warm water; very hot surface layers can push them deeper. |
| Cold | Active across a wide range; below 18°C feeding still possible but weaker. |
| Tide | Weak — oceanic species; tide is not a strong driver offshore. |
| Night | High — strong night feeder and known to aggregate around light. |
| Surface feeding | Strong — surface and subsurface strikes on bait balls. |

---

### 8. Octopus — *Octopus spp.*

- Preferred temperature: **22–30°C**
- Preferred depth: **5–60 m**
- Preferred current: **0.05–0.4 m/s**
- Typical habitat: **Inshore / Rocky & sandy bottom**
- Conservation status: **data_deficient**
- Legal catch status: **regulated**
- Natural range box: **12.0°–21.0° N, 68.0°–74.5° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Post-monsoon to winter — active on structure and sheltered grounds. |
| Monsoon off-season | Mid-monsoon: may hold in sheltered rocky/crevice habitat. |
| Rain | Not strongly rain-driven; more tied to shelter and bottom-type habitat. |
| Storm | High in sheltered structure; avoids open-bay surge. |
| Hot | Warm water suits activity; extreme heat can push them deeper into shade. |
| Cold | Below 21°C activity tends to slow. |
| Tide | Moderate — often forages on tide changes near structure. |
| Night | High — many octopus species are more active after dark. |
| Surface feeding | Low — benthic predator; not a surface feeder. |

---

### 9. Sea Bass — *Lates calcarifer*

- Preferred temperature: **24–32°C**
- Preferred depth: **2–50 m**
- Preferred current: **0.05–0.5 m/s**
- Typical habitat: **Estuarine / Coastal**
- Conservation status: **least_concern**
- Legal catch status: **regulated**
- Natural range box: **12.0°–21.0° N, 68.0°–75.0° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Pre-monsoon and post-monsoon — strong estuarine and nearshore feeding. |
| Monsoon off-season | Mid-monsoon: fish may move between estuaries and coastal holes with the rain and freshwater flow. |
| Rain | Prefers rain-associated freshwater flow; often moves into estuaries and creeks with runoff. |
| Storm | Moderate — holds in sheltered estuary channels during heavy weather. |
| Hot | Tolerates very warm water; thrives in hot estuarine conditions. |
| Cold | Below 23°C feeding tends to slow. |
| Tide | Strong — moves with tide into estuaries, creeks and coastal shallows. |
| Night | High — strong night and low-light feeder. |
| Surface feeding | Moderate to strong — known to take surface lures in estuaries. |

---

### 10. Tiger Prawn — *Penaeus monodon*

- Preferred temperature: **24–31°C**
- Preferred depth: **5–70 m**
- Preferred current: **0.05–0.4 m/s**
- Typical habitat: **Inshore / Estuarine / Muddy bottom**
- Conservation status: **least_concern**
- Legal catch status: **regulated**
- Natural range box: **13.0°–20.5° N, 68.5°–74.0° E**

| Trigger | Expected behavior |
|---|---|
| Monsoon peak | Southwest monsoon to post-monsoon — peak estuarine and mudflat productivity. |
| Monsoon off-season | Winter: still present in sheltered estuarine and mudflat grounds. |
| Rain | Prefers rain — estuarine flushing and mudflat productivity are key drivers. |
| Storm | High in sheltered water; avoids open-bay surge during storms. |
| Hot | Warm water suits growth; extreme heat can push deeper in the water column in shallow bays. |
| Cold | Below 23°C activity slows; estuary-fed grounds remain best. |
| Tide | Strong — moving tides and tide changes concentrate prawns in channels and edges. |
| Night | High — many penaeid prawns are more active and move up at night. |
| Surface feeding | Low — bottom and mid-water feeder. |

---

## Notes for editors

- If you change a numeric range in `species_db.py`, update the "Preferred environment" line here too.
- The "Natural range box" should track `natural_lat_min`, `natural_lat_max`, `natural_lng_min`, `natural_lng_max`.
- The trigger rows should track the env-behavior fields: `monsoon_peak`, `monsoon_off`, `prefers_rain`, `storm_tolerance`, `hot_behavior`, `cold_behavior`, `tide_affinity`, `night_activity`, `surface_feed_behavior`.
- This dataset is editorial. The prediction model currently uses the numeric ranges and the rule-based helpers in `species_db.py`; the trigger wording is what the reader sees.
