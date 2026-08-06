# Compendium Analect

[![Code of Conduct](https://img.shields.io/badge/Code%20of%20Conduct-Contributor%20Covenant-blue.svg)](CODE_OF_CONDUCT.md)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Published collections of contra dance choreography, prepared for import into
[Caller's Compendium](https://github.com/ibanner56/CallersCompendium).

Served from **<https://analect.callerscompendium.com/>**.

> **Status: early setup.** The repository structure and its governance are in
> place; the publishing pipeline (signing, manifest generation, and the content
> gate) is being implemented under
> [CallersCompendium#862](https://github.com/ibanner56/CallersCompendium/issues/862).
> Nothing is published yet.

*Analect* — from the Greek *analekta*, "things gathered up": a collection of
passages gathered from a larger body of work.

## What this is for

Caller's Compendium starts you with an empty collection. That is the right
default — it is your collection — but it means every new caller begins by typing
in dances they already know, or hunting for them one at a time.

This repository fixes that. It hosts curated, versioned collections that the app
can offer as a single import: a published book, a traditional repertoire, a
festival's programme. You pick one from a list in the app and it arrives whole.

## How it works

The app fetches a **manifest** from this site listing the available collections.
Each entry names an archive and carries its SHA-256. The manifest is signed with
a detached **Ed25519** signature, verified in-app against a pinned public key
before anything is read; the digest then covers each archive in turn. A manifest
that does not verify is refused outright.

Adding a collection therefore requires **no app release** — it appears in the
app as soon as it is published here.

The signing key used here is **separate from the one that signs application
updates**, so a problem with collection publishing can never affect update
delivery.

## Collections are immutable

Once published, a collection is never edited or removed. Corrections and
additions are published as a **new version** under a transparent suffix
(`example-1`, `example-2`), and the manifest records that the newer supersedes
the older.

This is deliberate. It means a content digest stays valid forever, a signature
never needs re-issuing, and a caller who imported `example-1` can be told
precisely what they have — not merely what they might have had.

## What a collection may contain

**Choreography — yes.** Figures, titles, formations, authorship and the other
structural facts of a dance. Per the U.S. Copyright Office's *Compendium of
Practices*, the choreography of a social dance is not itself copyrightable.

**Written commentary — only with permission.** Teaching notes, histories,
dedications, calling tips and similar prose **remain the intellectual property
of their author**. A collection may include them only when it carries an
explicit permission or licence record naming who granted it and on what terms.

Absence of such a record is a hard failure, not a warning. See
[CONTRIBUTING.md](CONTRIBUTING.md) for what a declaration must cover.

## Layout

| path | contents |
|---|---|
| `collections/` | published collection archives, one directory per version |
| `site/` | the static site published to GitHub Pages, including `CNAME` |
| `docs/` | publishing process and format notes |
| `.github/` | issue and PR templates, CI |

## Contributing

Proposals for new collections are welcome — particularly traditional and
public-domain repertoire, and works whose authors are willing to see them
shared. Start with [CONTRIBUTING.md](CONTRIBUTING.md); it covers what a
collection needs, what it may not contain, and how permission is recorded.

Please read the [Code of Conduct](CODE_OF_CONDUCT.md) before taking part, and
[SECURITY.md](SECURITY.md) if you have found something exploitable.

## Related

- [Caller's Compendium](https://github.com/ibanner56/CallersCompendium) — the app
- [CallersCompendium#862](https://github.com/ibanner56/CallersCompendium/issues/862)
  — the design this repository implements
