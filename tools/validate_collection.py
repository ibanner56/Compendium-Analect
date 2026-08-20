#!/usr/bin/env python3
"""Merge gate for published collections.

Runs on every pull request. Refuses a collection that carries written
commentary without a permission declaration covering it, that mutates an
already-published collection, or that contains any field this gate has not
been taught to classify.

Pure stdlib on purpose: this repository publishes archives, not tooling, and a
gate that needed the Dart SDK would be a gate people are tempted to skip.

CallersCompendium#862 is the authoritative design record.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys

# --- Field classification -------------------------------------------------
#
# Exhaustive over every key the app's `encodeArchive` emits for a dance. The
# gate is driven by the keys actually present in the submitted file, so an
# archive produced by a newer app carrying a field absent from this table
# FAILS rather than shipping unreviewed. Do not add a key here without
# deciding what it is.

CHOREOGRAPHY = "choreography"   # publishable: choreography is not copyrightable
ATTRIBUTION = "attribution"     # publishable: facts about authorship/publication
COMMENTARY = "commentary"       # NOT publishable without a permission declaration
LOCAL = "local"                 # meaningless in someone else's collection

DANCE_FIELDS = {
    "id": CHOREOGRAPHY,
    "title": CHOREOGRAPHY,
    "form": CHOREOGRAPHY,
    "formation": CHOREOGRAPHY,
    "progression": CHOREOGRAPHY,
    "phraseStructure": CHOREOGRAPHY,
    "figures": CHOREOGRAPHY,
    "mixer": CHOREOGRAPHY,
    "authorIds": ATTRIBUTION,
    "sourceCitations": ATTRIBUTION,
    "composedOn": ATTRIBUTION,
    "revisedOn": ATTRIBUTION,
    "provenance": ATTRIBUTION,
    "hook": COMMENTARY,
    "callingNotes": COMMENTARY,
    "walkthrough": COMMENTARY,
    "customFields": COMMENTARY,
    "links": COMMENTARY,
    "tunes": COMMENTARY,
    "status": LOCAL,
    "level": LOCAL,
    "mixedLevel": LOCAL,
    "rating": LOCAL,
    "tagIds": LOCAL,
    "createdAt": LOCAL,
    "updatedAt": LOCAL,
    "deletedAt": LOCAL,
}

COMMENTARY_FIELDS = {k for k, v in DANCE_FIELDS.items() if v == COMMENTARY}

# A collection directory's version suffix is visible in the path on purpose,
# so which version something is can be read off a file path alone.
COLLECTION_DIR = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-(\d+)$")


class Failure(Exception):
    pass


def fail(msg: str) -> None:
    raise Failure(msg)


def is_present(value) -> bool:
    """Whether a field actually carries content."""
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


# --- Permission declarations ---------------------------------------------

REQUIRED_DECLARATION_KEYS = {"grantedBy", "role", "date", "terms", "coversFields"}


def load_declaration(path: pathlib.Path):
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path}: not valid JSON ({exc})")
    if not isinstance(data, dict):
        fail(f"{path}: expected a JSON object")

    missing = REQUIRED_DECLARATION_KEYS - data.keys()
    if missing:
        fail(f"{path}: declaration missing required key(s): {sorted(missing)}")

    covers = data["coversFields"]
    if not isinstance(covers, list) or not covers:
        fail(f"{path}: coversFields must be a non-empty list")
    # Each entry must be a string before the `in` membership check below: an
    # unhashable entry (a list or dict a contributor pasted in by mistake)
    # would otherwise raise TypeError and crash the gate instead of refusing
    # cleanly, which is the failure mode this validator exists to prevent.
    non_strings = [f for f in covers if not isinstance(f, str)]
    if non_strings:
        fail(
            f"{path}: coversFields must contain only strings, got "
            f"{non_strings!r}"
        )
    unknown = [f for f in covers if f not in COMMENTARY_FIELDS]
    if unknown:
        fail(
            f"{path}: coversFields names field(s) that are not commentary: "
            f"{unknown}. Only {sorted(COMMENTARY_FIELDS)} need a declaration."
        )
    for key in ("grantedBy", "role", "terms"):
        if not isinstance(data[key], str) or not data[key].strip():
            fail(f"{path}: '{key}' must be a non-empty string")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(data["date"])):
        fail(f"{path}: 'date' must be YYYY-MM-DD, got {data['date']!r}")
    return data


# --- Archive validation ---------------------------------------------------


def _count_notes(figures) -> int:
    """Count figure notes, descending into `meanwhile` containers.

    A `meanwhile` figure holds its simultaneous sides in `params.figures`, so a
    top-level-only walk cannot see a note attached to either side. On the first
    real collection that hid 11 of 87 notes.

    This number is reviewer-facing: it is the basis on which a human confirms
    that no note is author commentary. An undercount here does not fail the
    gate loudly, it quietly shrinks what the reviewer believes they are
    confirming -- which is the worse failure, because it looks like diligence.
    """
    total = 0
    for figure in figures or []:
        if not isinstance(figure, dict):
            continue
        if is_present(figure.get("note")):
            total += 1
        params = figure.get("params")
        if isinstance(params, dict):
            total += _count_notes(params.get("figures"))
    return total


def validate_archive(archive_path: pathlib.Path, declaration):
    notes = []
    try:
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{archive_path}: not valid JSON ({exc})")
    if not isinstance(archive, dict):
        fail(f"{archive_path}: expected a JSON object")
    if "schemaVersion" not in archive:
        fail(f"{archive_path}: missing schemaVersion")

    dances = archive.get("dances")
    if not isinstance(dances, list) or not dances:
        fail(f"{archive_path}: archive contains no dances")

    covered = set(declaration["coversFields"]) if declaration else set()
    uncovered = {}
    unclassified = set()
    figure_notes = 0

    for dance in dances:
        if not isinstance(dance, dict):
            fail(f"{archive_path}: a dance entry is not an object")
        title = dance.get("title", "<untitled>")

        for key, value in dance.items():
            kind = DANCE_FIELDS.get(key)
            if kind is None:
                unclassified.add(key)
                continue
            if kind == COMMENTARY and is_present(value) and key not in covered:
                uncovered.setdefault(key, []).append(title)

        raw_figures = dance.get("figures")
        if raw_figures is not None and not isinstance(raw_figures, list):
            fail(
                f"{archive_path}: dance '{title}' has a malformed 'figures' "
                f"value (expected a list, got {type(raw_figures).__name__}). "
                "The figure-note count is reviewer-facing; an unexpected type "
                "must be fixed rather than silently ignored."
            )
        figure_notes += _count_notes(raw_figures or [])

    if unclassified:
        fail(
            f"{archive_path}: unclassified dance field(s): {sorted(unclassified)}.\n"
            "  The app has added a field this gate has not been taught to judge.\n"
            "  Classify it in DANCE_FIELDS before publishing anything. Do NOT\n"
            "  delete the field from the archive to make this pass."
        )

    if uncovered:
        lines = [f"{archive_path}: written commentary with no permission covering it:"]
        for field, titles in sorted(uncovered.items()):
            shown = ", ".join(titles[:3])
            more = f" (+{len(titles) - 3} more)" if len(titles) > 3 else ""
            lines.append(f"  - {field}: {len(titles)} dance(s) - {shown}{more}")
        lines.append("")
        lines.append(
            "  Choreography is not copyrightable; the author's prose is. Either\n"
            "  remove this content, or add permission.json declaring who granted\n"
            "  permission and on what terms, with coversFields naming each field\n"
            "  above. The gate never strips content for you - a silent strip would\n"
            "  let you believe you had published notes that had in fact vanished."
        )
        fail("\n".join(lines))

    if figure_notes:
        # Figure notes are transcription (a source's own figure-line text such
        # as "face next", or a compound's shorthand parent name), so they are
        # classified as choreography. The gate cannot tell transcription from
        # prose smuggled into the same slot, so it surfaces the count for a
        # human reviewer rather than guessing either way.
        notes.append(
            f"{figure_notes} figure note(s) present - transcription, not gated. "
            "Reviewer: confirm none are author commentary."
        )
    return notes


# --- Immutability ---------------------------------------------------------


def _collection_of(path: str) -> str:
    """The collection directory `path` lives in, or "" if it is not in one.

    Only `collections/<name>/<something>` names a collection. A file sitting
    directly in `collections/` (`collections/README.md`) is repository
    furniture, not a published collection, and must not be mistaken for one --
    a naive `split("/")[1]` reads it as a collection called "README.md".
    """
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != "collections":
        return ""
    return parts[1]


def check_immutability(base_ref: str):
    """A published collection is never edited or deleted (decision 4)."""
    try:
        out = subprocess.run(
            ["git", "diff", "--name-status", f"{base_ref}...HEAD", "--", "collections/"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        fail(f"could not diff against {base_ref}: {exc.stderr.strip()}")

    existing = set(
        subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", base_ref, "collections/"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
    )
    # The collection directories that already exist on base_ref. Immutability
    # is a property of the whole directory, not just of the files in it: a NEW
    # file added under an already-published collection changes what that
    # collection is, and its digest, without touching any existing file.
    existing_collections = {_collection_of(p) for p in existing} - {""}

    violations = []
    for line in out.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("A"):
            path = parts[1] if len(parts) > 1 else ""
            collection = _collection_of(path)
            if collection and collection in existing_collections:
                # A branch can be based on a commit behind its remote base.
                # If it adds a byte-identical metadata file that is already on
                # base_ref, it is a harmless reconciliation, not a mutation.
                try:
                    base_blob = subprocess.run(
                        ["git", "rev-parse", f"{base_ref}:{path}"],
                        capture_output=True, text=True, check=True,
                    ).stdout.strip()
                    head_blob = subprocess.run(
                        ["git", "rev-parse", f"HEAD:{path}"],
                        capture_output=True, text=True, check=True,
                    ).stdout.strip()
                except subprocess.CalledProcessError:
                    base_blob = head_blob = ""
                if base_blob and base_blob == head_blob:
                    continue
                if path.endswith(("collection.json", "permission.json")):
                    try:
                        base_bytes = subprocess.run(
                            ["git", "show", f"{base_ref}:{path}"],
                            capture_output=True, check=True,
                        ).stdout
                        head_bytes = pathlib.Path(path).read_bytes()
                    except (subprocess.CalledProcessError, OSError):
                        base_bytes = head_bytes = b""
                    if base_bytes.rstrip() == head_bytes.rstrip():
                        continue
                violations.append(f"  {status} {path}")
            continue  # adding a whole new collection is the normal case
        # For rename (Rxxx) and copy (Cxxx) lines git emits two paths:
        # old-path and new-path. We check both: the old path was a published
        # file being renamed/moved (immutability violation), and the new path
        # could overwrite one.
        paths_to_check = parts[1:]  # one path for M/D, two for R/C
        for path in paths_to_check:
            if not _collection_of(path):
                continue
            if path in existing:
                violations.append(f"  {status} {path}")

    if violations:
        fail(
            "published collections are immutable - these changes alter a "
            f"collection that already exists on {base_ref}:\n" +
            "\n".join(violations) +
            "\n\n  Publish a correction as a NEW version directory instead. A "
            "digest that\n  stays valid forever, and a user's record of what they "
            "imported, both\n  depend on this."
        )
    return []


# --- Entry point ----------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="", help="git ref to compare against")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args()

    root = pathlib.Path(args.root)
    collections = root / "collections"
    failures = []

    dirs = sorted(p for p in collections.iterdir() if p.is_dir()) if collections.is_dir() else []
    if not dirs:
        print("no collections present; nothing to validate")
    for directory in dirs:
        print(f"\n=== {directory.name} ===")
        try:
            if not COLLECTION_DIR.match(directory.name):
                fail(
                    f"collections/{directory.name}: name must end in a visible "
                    "version suffix, e.g. 'barnes-1'"
                )
            archive = directory / "archive.json"
            if not archive.exists():
                fail(f"{directory}: missing archive.json")
            declaration = load_declaration(directory / "permission.json")
            got = validate_archive(archive, declaration)
            if declaration:
                print(
                    f"  permission: {declaration['grantedBy']} "
                    f"({declaration['role']}) covers {declaration['coversFields']}"
                )
            for note in got:
                print(f"  note: {note}")
            print("  OK")
        except Failure as exc:
            print(f"  FAIL: {exc}")
            failures.append(directory.name)

    if args.base_ref:
        print("\n=== immutability ===")
        try:
            check_immutability(args.base_ref)
            print("  OK - no published collection was modified or deleted")
        except Failure as exc:
            print(f"  FAIL: {exc}")
            failures.append("immutability")

    print()
    if failures:
        print(f"GATE FAILED: {', '.join(failures)}")
        return 1
    print(f"GATE PASSED: {len(dirs)} collection(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
