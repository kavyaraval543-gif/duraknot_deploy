# Simulator calibration — sourced benchmarks

No hardware was streaming real sensor data at the time of writing, so the
dashboard's built-in simulator (`sim` object in `index.html`) stands in.
Rather than picking numbers arbitrarily, its constants were checked against
published industry benchmarks so the demo output is defensible, not just
plausible-looking. This file is the paper trail.

## Line speed — `IDEAL_RATE = 14.0` m/min

Welded wire mesh machines: entry-level models run 10–20 m/min, high-end
systems exceed 50 m/min. 14.0 m/min sits in the entry/mid band, appropriate
for a single-line pilot deployment rather than a high-end multi-line plant.

- [Wire Fence Making Machine Buying Guide — Alibaba](https://smartbuy.alibaba.com/buyingguides/wire-fence-making-machine)
- [Chain Link Fence Weaving Machine — Accio](https://www.accio.com/plp/chain-link-fence-weaving-machine)

## Defect rate — `sim.tick()` base defect probability

Industry-cited "qualified rate" for welded wire mesh is 98% for domestic
orders (100% for export-grade), i.e. roughly a 2% accepted defect rate.
The simulator's base per-second defect probability (0.03, with a 2% chance
per tick of a burst period at 0.40) averages out close to that figure over
a shift.

- [Welded Wire Mesh Standard — weldedwiresupplier.com](https://www.weldedwiresupplier.com/technology/wire-panel-manufacturing-standard.html)
- [Wire Mesh Quality Control Points — Anpinglobal](https://www.anpinglobal.com/en/blog/wire-mesh-quality-control-points/)

## Downtime / availability — `sim.tick()` stoppage probability

PwC (2023) puts discrete-manufacturing downtime at ~5.7% of planned
production time; a 2020 NIST study found ~7.8%. The simulator's stoppage
trigger (1.2%/sec chance of a 4–9s stoppage) works out to roughly 6–7%
downtime over a shift — inside that 5.7–7.8% band. Nakajima's classic
90% availability figure (the "A" in the 90% × 95% × 99% = 85% world-class
OEE decomposition) is the reference point the dashboard's Availability
gauge is read against.

- [Unplanned Downtime Frequency Benchmarks — Reliamag](https://reliamag.com/guides/unplanned-downtime-frequency-benchmarks/)
- [OEE Benchmarks: Realistic Values by Industry — Symestic](https://www.symestic.com/en-us/blog/oee/oee-benchmarks)

## OEE tiers — dashboard legend text

Replaces the old single "typical discrete manufacturing 60%" line with the
actual tiered benchmark:

| Tier | OEE range |
|---|---|
| Global average | 55–70% |
| Advanced | 70–80% |
| World-class (top 5–10% of plants) | 80%+ (85% is the classic Nakajima figure) |

- [OEE Benchmarks by Manufacturing Industry Vertical — Godlan](https://godlan.com/oee-benchmark-industry/)
- [What Is World Class OEE? — Tractian](https://tractian.com/en/blog/world-class-oee)

## What this doesn't cover

These sources calibrate the *simulator's* statistical parameters, not a
claim about the real Duraknot line's actual performance — that number can
only come from running the real sensor node (`firmware/duraknot_esp32.ino`)
on the physical line, which is exactly what the pilot phase in the
implementation roadmap is for.
