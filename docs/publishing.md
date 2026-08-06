# Publishing

> **Not yet implemented.** This records the agreed design so the repository's
> structure makes sense before the tooling exists. The pipeline is being built
> under [CallersCompendium#862](https://github.com/ibanner56/CallersCompendium/issues/862);
> that issue is the authoritative record.

## Trust model

The **manifest** is signed with a detached **Ed25519** signature over its exact
bytes, verified in the app against a **pinned public key**. The manifest carries
a **SHA-256 for each archive**, so one signature transitively covers all
published content. Archives are not signed individually.

The signing key is **separate from the key that signs application updates**. The
update key signs installers; sharing it would mean a compromise of collection
publishing could become code execution on every user's machine.

Rotating a pinned key requires shipping the new public key in an **app release
first**, because older clients pin the old one. That constraint now applies to
two keys.

## Immutability

A published collection is never edited or deleted. Corrections ship as a new
version under a visible suffix, and the manifest records supersession.

This is what lets a digest stay valid indefinitely, spares every collection from
re-signing, and keeps a user's record of what they imported permanently true.

## The content gate

CI fails a collection that carries written commentary — `hook`, `callingNotes`,
`walkthrough`, or free-text custom fields — **without** a permission or licence
declaration.

The gate **fails**; it does not silently strip. A strip would let a contributor
believe they had published notes that had in fact vanished.

Note what the gate can and cannot do. It checks that a declaration **was made**,
is **well formed**, and **covers the fields actually present**. It cannot check
that the claim is true — a human reviewer must still agree. A green check is not
a legal opinion.

The field classification is **exhaustive**, mirroring the app's
`data_classification_coverage_test`: a newly added field cannot ship
unclassified.

## Manifest schema

The **app repository owns the schema**; its parser is the spec of record. This
repository vendors it.

Parsing **ignores unrecognised fields** and refuses only on an explicit **major**
version bump. This matters because producer and consumer are in different
repositories on independent release cadences: the app's *update* manifest can
safely demand an exact version match because its producer and consumer ship
together, but that same strictness here would mean a schema bump silently
stopped every already-installed app from seeing any collection at all.

A published collection should therefore state the minimum schema version it
requires.

## Site publishing

`site/` deploys via `actions/deploy-pages`, where the artifact is the complete
published state.

The app repository deliberately does the opposite — a branch push that preserves
files it does not own — because two independent writers share its `gh-pages`
branch. This repository has no such split, so the simpler flow is correct here.

**One consequence to respect:** because the artifact *is* the published state,
anything not in it is dropped. `site/CNAME` must therefore stay tracked in this
repository — a custom domain set only in repo settings will be cleared by the
next deploy. See CallersCompendium#863 for the same bug caught in the app repo.
