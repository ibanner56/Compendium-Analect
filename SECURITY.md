# Security Policy

Thanks for helping keep Compendium Analect and its users safe. This document
explains how to report a security problem and what to expect afterward.

This repository publishes content that thousands of installations may import on
the strength of a signature. The signing key and the publishing pipeline are
therefore the parts that matter most here — a flaw in either affects everyone
who imports a collection.

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** — don't open a public
issue, PR, or discussion for something exploitable.

- **Preferred:** GitHub's [private vulnerability reporting][pvr]. Go to the
  repository's **Security** tab → **Report a vulnerability**, and file a private
  advisory. This keeps the report confidential and threads the whole
  conversation in one place.
- **Fallback:** if you can't use that (or aren't sure it's enabled yet), email
  the maintainer at **compendium@contra.dance** with "SECURITY" in the subject.

Helpful things to include: what you found, how to reproduce it, and the impact
you think it has. A proof of concept is great but never required.

[pvr]: https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability

## Especially interested in

- Anything that would let an **unsigned or altered** collection be accepted by
  the app — signature bypass, digest mismatch not being enforced, or a manifest
  that verifies when it shouldn't.
- Anything that could **substitute one collection for another**, including
  replay of a superseded version presented as current.
- Weaknesses in how the **signing key** is stored, used, or exposed by CI.
- A path that lets a collection be **edited or removed after publication**,
  since immutability is what the digests and the app's records rely on.

## What to expect

This project is maintained by one person in their spare time, so please set your
expectations accordingly:

- **Acknowledgement:** I aim to reply within about **7 days**.
- **Assessment & fix:** timelines depend on severity and my availability. I'll
  keep you updated on the advisory thread and let you know the plan.
- **Disclosure:** I prefer coordinated disclosure — let's agree on timing before
  any public write-up, and I'm happy to credit you (or keep you anonymous, your
  call).

If you don't hear back within a couple of weeks, a gentle nudge is welcome.

## Not a security issue

Some things are genuinely important but belong in a normal issue, or in an email
if they shouldn't be public:

- A **mistake in a dance** — a wrong figure, a bad title. File an issue.
- A **copyright, attribution or permission** problem. Email
  **compendium@contra.dance**; these are handled urgently but they are not
  vulnerabilities, and the private-advisory workflow is a poor fit.

## Supported versions

Published collections are **immutable** and are never patched in place. A
security-relevant correction is published as a **new version**, and the manifest
records that it supersedes the old one.

There is no way to un-publish something a user has already imported, which is
precisely why the review gate matters more here than a patch process would.

## No bug bounty

There's no paid bounty program — this is a free, open-source, solo-maintained
project. Responsible disclosure is genuinely appreciated, and I'm glad to
acknowledge reporters in the advisory and release notes.
