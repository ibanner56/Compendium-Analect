# Contributing to Compendium Analect

Thanks for helping build the shared repertoire. This repository is unusual for a
software project: most of what it holds is **content**, and the rules that
matter most here are about provenance and permission rather than code style.

Please read the [Code of Conduct](CODE_OF_CONDUCT.md) first — it applies
everywhere in this project.

## Ground rules

- **Choreography is welcome. Someone else's prose is not, unless they said yes.**
  This is the single rule that matters most; the rest of this document is mostly
  detail on how it is enforced.
- **Never edit a published collection.** Corrections ship as a new version.
- **Be honest about sources.** Where a dance came from, and who wrote it, is
  part of the record.
- **Know what you are and aren't granting.** Contributing a collection is not a
  copyright grant — for choreography there is nothing to grant. See
  [LICENSING.md](LICENSING.md).

## What a collection may contain

### Choreography — yes

Figures, titles, formations, progression, phrase structure, authorship and the
other structural facts of a dance.

The U.S. Copyright Office's *Compendium of Practices* is explicit that the
choreography of a social dance is not itself copyrightable. Transcribing what a
dance *does* is therefore not an infringement, even when the dance appears in a
published book.

### Written commentary — only with recorded permission

Teaching notes, histories, dedications, calling advice and similar prose
**remain the intellectual property of their author**, whatever the status of the
choreography they accompany. Concretely, in Caller's Compendium's data model,
these fields:

- `hook`
- `callingNotes`
- `walkthrough`
- custom fields carrying free text

A collection may include them **only** when it carries a permission or licence
declaration that names who granted the permission and on what terms, and that
covers the fields actually present.

Three things follow, and they are worth stating plainly:

1. **No declaration means the collection is rejected**, not stripped. A silent
   strip would let a contributor believe they had published notes that had in
   fact vanished.
2. **A partial declaration does not wave through the rest.** If permission
   covers `callingNotes` but the collection also carries `walkthrough`, that is
   a failure.
3. **The gate checks that a claim was made and is well formed. It cannot check
   that the claim is true.** A human reviewer still has to agree. Do not treat a
   green check as a legal opinion.

### Being your own author

If you wrote the dances *and* the notes, you hold both rights and may publish
both — but the declaration is still required. It is the record of *why* the
prose is there, and future maintainers will need it long after the context is
forgotten.

## Proposing a collection

1. **Open an issue first** using the *Propose a collection* template. Describe
   the source, who the author is, roughly how many dances, and what permission
   exists for any prose. This is much cheaper than preparing an archive that
   cannot be accepted.
2. **Agree the scope** in the issue — particularly whether commentary is
   included and what the declaration will say.
3. **Open a pull request** adding the collection under `collections/`.

## Versioning

Collections are **immutable**. Once a version is merged it is never edited or
removed.

A correction — a wrong figure, a misspelled title, a dance to add — is published
as a **new version** with a transparent suffix:

```
collections/example-1/
collections/example-2/     <- supersedes example-1
```

The manifest records the supersession, so the app can tell a caller who imported
`example-1` that `example-2` exists.

This is stricter than it may seem necessary, and deliberately so. Immutability
is what lets a published digest stay valid indefinitely, and it means "I
imported this collection" remains a true statement forever rather than a claim
about a moving target.

**Practical consequence:** a pull request that modifies or deletes anything
under an existing `collections/<name>-<n>/` directory will be rejected. Add a
new version instead.

## Review

Every collection PR is reviewed for:

- **Provenance** — is the source identified, and is the attribution right?
- **Permission** — if prose is present, is the declaration real, specific, and
  does it cover everything present?
- **Accuracy** — do the figures match the source?
- **Immutability** — does it add a version rather than change one?

Automated checks cover the mechanical parts (structure, field classification,
digest, immutability). They are a floor, not a substitute for the review above.

## Reporting a problem with a published collection

Open an issue using the *Report a collection problem* template. Because
collections are immutable, the fix is a new version rather than an edit — but a
report is still exactly the right thing to file, and errors of attribution or
permission are taken seriously and handled quickly.

If the problem is a **permission or copyright** matter, or anything else where
public discussion would be inappropriate, email **compendium@contra.dance**
instead of opening an issue.

## Security

Please report suspected vulnerabilities privately — see
[SECURITY.md](SECURITY.md). The signing key and the publishing pipeline are the
sensitive parts of this repository; a flaw there affects everyone who imports a
collection.
