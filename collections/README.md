# Collections

One directory per published collection **version**. Nothing here is ever edited
or deleted once merged — a correction is a new version.

```
collections/
  example-1/
  example-2/    <- supersedes example-1
```

The naming suffix is deliberately visible rather than hidden in metadata, so it
is obvious from a file path alone which version something is.

The `foda-1-1` collection is published by the Pages workflow at
<https://analect.callerscompendium.com/collections/manifest.json>. The feed is
signed with a detached Ed25519 signature and contains immutable, dance-only v1
archives for CallersCompendium PR #1007.

Each version directory also contains the publication inputs:

```
collections/foda-1-1/
  archive.json       # app export; source metadata is mapped out for v1
  collection.json    # immutable identity, title, capabilities, licence
  permission.json    # grantor, basis, and commentary-field coverage
```

The generated archive contains dances and only the choreographers they
reference. Programs, venues, published sources, tags, custom fields, source
citations, and embedded published-collection provenance are refused by the
publication gate. Commentary is never silently removed: every populated
publishable field must be covered by the permission declaration, and custom
field content is refused because the app's v1 reader does not import it.

Archives and their manifest entries are immutable. A correction is a new
visible version directory (for example `foda-1-2`) with `supersedes` pointing
to `foda-1-1`; the generator derives the archive byte count, SHA-256, dance
count, and URL from the generated artifact rather than trusting metadata.

The Pages job needs the maintainer-held `ANALECT_SIGNING_KEY_B64`
secret. The private key is never committed or printed.
