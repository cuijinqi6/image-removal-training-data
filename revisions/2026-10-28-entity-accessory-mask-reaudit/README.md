# Entity/accessory mask re-audit revision

This directory contains the **34 changed and validated samples** from
the 2026-10-28 re-audit. It is an incremental revision; the original
134-sample dataset outside this directory remains unchanged.

Changed masks add reviewed physical accessories that belong to the selected
people: umbrellas, backpacks, handbags, hand-held items, ride-on equipment and
other connected possessions. Cast shadows and environment reflections are not
part of the training entity mask. The target still removes the selected object,
its attached possessions, associated shadows and reflections.

Samples 108 and 138 were reviewed but required no changes, so they are omitted.
Samples still marked `needs_review` or otherwise not accepted are excluded.

`comparison/` contains three-panel input/mask/target images. `manifest.json`
records the review notes and SHA-256 hashes for all four payloads per sample.
