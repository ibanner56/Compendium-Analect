# Contributing a collection

A collection is one directory under `collections/`, named with a **visible
version suffix** (`barnes-1`, `barnes-2`), containing:

```
collections/<id>-<version>/
  archive.json        required — a Caller's Compendium archive
  collection.json     required — immutable id, SemVer version, title, licence
  permission.json     required — manifest permission and commentary coverage
```

Open a pull request. The **Collection gate** runs automatically and must pass.

## What the gate refuses, and why

**Written commentary with no permission covering it.** Dance choreography is
not copyrightable (US Copyright Office, *Compendium of Practices*), so figures
publish freely. The prose *around* a dance — `hook`, `callingNotes`,
`walkthrough`, custom fields — remains the author's intellectual property.

The gate **fails**; it never strips. A silent strip would let you believe you
had published notes that had in fact vanished.

**Partial permission does not wave through the rest.** A declaration covering
`callingNotes` does not license a `hook`. Every commentary field actually
present must be named.

**A field the gate has not been taught to classify.** If the app gains a new
`Dance` field, the gate stops rather than publishing it unreviewed. Classify
it in `DANCE_FIELDS` — do not delete the field from your archive to get green.

**Any edit or deletion of an already-published collection.** Collections are
immutable. Publish a correction as a new version directory. This is what lets
a digest stay valid forever and keeps a user's record of what they imported
permanently true.

The v1 publication archive contains dances and referenced choreographers only.
Non-empty programs, venues, published sources, tags, top-level custom fields,
dance custom fields, and source citations are rejected, as are unknown
top-level entities, missing or duplicate dance ids, unreferenced choreographers,
and embedded published-collection provenance. Composite phrase structures must
declare `compositePhraseStructureV1` in `collection.json`.

## Declaring permission

```json
{
  "grantedBy": "Jane Caller",
  "role": "author",
  "date": "2026-08-06",
  "terms": "CC BY-NC 4.0, per the collection's front matter.",
  "coversFields": ["callingNotes", "hook"]
}
```

Be precise about what this does and does not establish. The gate checks that a
declaration **was made**, is **well formed**, and **covers the fields actually
present**. It cannot check that the claim is **true** — a human reviewer must
still agree. **A green check is not a legal opinion.**

If you are not the author, say who granted permission and how you obtained it.

## Figure notes

A `note` on a figure is transcription — a source's own figure-line text such
as `face next`, or a compound figure's shorthand name — so it publishes with
the choreography. The gate cannot tell transcription from prose put in the
same slot, so it **reports the count** and leaves the judgement to a reviewer.
Do not use figure notes to carry commentary.

## Running the gate locally

```sh
python3 -m unittest discover -s tools -p 'test_*.py'
python3 tools/validate_collection.py --base-ref origin/main
```

No dependencies beyond Python 3. That is deliberate: this repository publishes
archives, not tooling, and a gate needing a toolchain is a gate people skip.

## Signing

Publishing is signed by a maintainer with a key held in a protected
environment that requires human approval before it runs. The signature asserts
that a maintainer **reviewed and approved** the archive and that its
provenance is clean — so it is applied after review, never automatically on
merge.

The Pages workflow reads base64-encoded PEM, DER, or raw Ed25519 seed
material from the `ANALECT_SIGNING_KEY_B64` Actions secret. Do not add a key to a pull
request or local repository; unsigned local generation uses
`tools/publish_collections.py --no-sign`.
