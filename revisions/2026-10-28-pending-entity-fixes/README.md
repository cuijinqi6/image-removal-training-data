# Follow-up entity mask fixes

Five reviewed mask revisions: 132 (shopping trolleys/possessions), 140 (hat and crossbody bag), 143 (bench bags/food belongings), 144 (exclude storefront glass reflection false instances), 150 (carried-bag edge). Their existing removal targets are retained after review. Fixed benches, environmental shadows and off-frame/unselected cafe patrons reflected in glass are excluded from the selected physical entities.

Manual object boundaries and semantic proposals are approximate. Every payload has a SHA-256 record. Sample 148 was reviewed unchanged: decorative balloon and boot/waterline false accessory proposals were excluded, so it is not copied here. Sample 127 remains unresolved at its cumulative request limit and is not included.

This supplements `../2026-10-28-entity-accessory-mask-reaudit/`. Original 134 baseline samples are unchanged. Full re-audit is still in progress.
