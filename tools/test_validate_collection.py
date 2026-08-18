#!/usr/bin/env python3
"""Tests for the collection merge gate.

Every failure mode is asserted to FAIL, not merely that the happy path
passes. A gate whose refusal path is untested is a gate that quietly stops
refusing.

Run: python3 -m unittest discover -s tools -p 'test_*.py'
"""

import json
import os
import pathlib
import subprocess
import tempfile
import unittest

from validate_collection import (
    COMMENTARY_FIELDS,
    DANCE_FIELDS,
    Failure,
    check_immutability,
    load_declaration,
    validate_archive,
)


def dance(**overrides):
    base = {
        "id": "d1",
        "title": "Test Dance",
        "authorIds": ["a1"],
        "form": "contra",
        "formation": {"shape": "dupleImproper"},
        "progression": "single",
        "phraseStructure": "",
        "figures": [{"schemaVersion": 1, "move": "swing", "params": {"beats": 16}}],
        "hook": "",
        "callingNotes": "",
        "walkthrough": "",
        "status": "active",
        "mixedLevel": False,
        "mixer": False,
        "tunes": [],
        "customFields": [],
        "tagIds": [],
        "links": [],
        "sourceCitations": [],
        "createdAt": "2000-01-01T00:00:00.000Z",
        "updatedAt": "2000-01-01T00:00:00.000Z",
    }
    base.update(overrides)
    return base


class GateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_archive(self, *dances):
        path = self.dir / "archive.json"
        path.write_text(json.dumps({"schemaVersion": 2, "dances": list(dances)}), encoding="utf-8")
        return path

    def write_declaration(self, **overrides):
        data = {
            "grantedBy": "Isaac Banner",
            "role": "author",
            "date": "2026-08-06",
            "terms": "Author is the rights holder and permits publication.",
            "coversFields": ["callingNotes"],
        }
        data.update(overrides)
        path = self.dir / "permission.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    # --- happy paths ---

    def test_choreography_only_passes(self):
        validate_archive(self.write_archive(dance()), None)

    def test_figure_note_count_sees_inside_a_meanwhile(self):
        # The count is reviewer-facing: a human confirms "none of these are
        # author commentary" against it. A top-level-only walk cannot see a
        # note on either side of a `meanwhile`, which hid 11 of 87 notes on the
        # first real collection -- silently shrinking what the reviewer was
        # actually confirming.
        archive = self.write_archive(
            dance(
                figures=[
                    {
                        "schemaVersion": 1,
                        "move": "swing",
                        "params": {"beats": 8},
                        "note": "top-level note",
                    },
                    {
                        "schemaVersion": 1,
                        "move": "meanwhile",
                        "params": {
                            "beats": 8,
                            "figures": [
                                {
                                    "schemaVersion": 1,
                                    "move": "allemande",
                                    "params": {"beats": 8},
                                    "note": "nested note one",
                                },
                                {
                                    "schemaVersion": 1,
                                    "move": "star",
                                    "params": {"beats": 8},
                                    "note": "nested note two",
                                },
                            ],
                        },
                    },
                ]
            )
        )
        notes = validate_archive(archive, None)
        self.assertTrue(notes, "expected a figure-note note")
        self.assertIn("3 figure note(s)", notes[0])

    def test_commentary_passes_when_declared(self):
        archive = self.write_archive(dance(callingNotes="robins look right"))
        decl = load_declaration(self.write_declaration())
        validate_archive(archive, decl)

    # --- the refusals ---

    def test_commentary_without_declaration_FAILS(self):
        for field in COMMENTARY_FIELDS:
            value = ["x"] if field in ("tunes", "customFields", "links") else "prose"
            with self.subTest(field=field):
                archive = self.write_archive(dance(**{field: value}))
                with self.assertRaises(Failure) as ctx:
                    validate_archive(archive, None)
                self.assertIn(field, str(ctx.exception))

    def test_partial_permission_does_not_wave_through_the_rest_FAILS(self):
        # Declaration covers callingNotes only; the dance also carries a hook.
        archive = self.write_archive(
            dance(callingNotes="fine", hook="written for Paul")
        )
        decl = load_declaration(self.write_declaration(coversFields=["callingNotes"]))
        with self.assertRaises(Failure) as ctx:
            validate_archive(archive, decl)
        self.assertIn("hook", str(ctx.exception))
        self.assertNotIn("- callingNotes", str(ctx.exception))

    def test_unclassified_field_FAILS(self):
        archive = self.write_archive(dance(someNewAppField="anything"))
        with self.assertRaises(Failure) as ctx:
            validate_archive(archive, None)
        self.assertIn("someNewAppField", str(ctx.exception))

    def test_empty_commentary_is_not_flagged(self):
        # An empty string / empty list is absence, not content.
        validate_archive(
            self.write_archive(dance(callingNotes="   ", tunes=[], links=[])), None
        )

    def test_malformed_declarations_FAIL(self):
        cases = {
            "missing key": {"grantedBy": "X"},
            "empty coversFields": {"coversFields": []},
            "non-commentary field": {"coversFields": ["figures"]},
            # A pasted-in-error non-string entry (e.g. a nested list or
            # object) is unhashable, so `f not in COMMENTARY_FIELDS` would
            # raise TypeError and crash the gate instead of refusing cleanly.
            "unhashable coversFields entry": {"coversFields": [["hook"]]},
            "bad date": {"date": "August 2026"},
            "blank grantor": {"grantedBy": "  "},
        }
        for name, overrides in cases.items():
            with self.subTest(case=name):
                if name == "missing key":
                    path = self.dir / "permission.json"
                    path.write_text(json.dumps(overrides), encoding="utf-8")
                else:
                    path = self.write_declaration(**overrides)
                with self.assertRaises(Failure):
                    load_declaration(path)

    def test_absent_declaration_is_not_an_error_by_itself(self):
        self.assertIsNone(load_declaration(self.dir / "permission.json"))

    def test_archive_must_contain_dances(self):
        path = self.dir / "archive.json"
        path.write_text(json.dumps({"schemaVersion": 2, "dances": []}), encoding="utf-8")
        with self.assertRaises(Failure):
            validate_archive(path, None)

    def test_classification_covers_every_commentary_field(self):
        # Guards the table itself: these four are named in CallersCompendium#862
        # as the commentary-bearing fields and must never silently reclassify.
        for field in ("hook", "callingNotes", "walkthrough", "customFields"):
            self.assertEqual(DANCE_FIELDS[field], "commentary", field)


if __name__ == "__main__":
    unittest.main()


class ImmutabilityTest(unittest.TestCase):
    """Exercises check_immutability() against a real git repository.

    These have to use real git: the function's inputs are `git diff
    --name-status` and `git ls-tree` output, and the status-A branch that
    handles additions is only ever reached when a diff actually contains an
    added file under collections/. A fixture that fakes the git output would
    not have caught the NameError this suite now guards, because the crash
    needed a genuine "A\tcollections/<published>/..." line to reach it.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self._cwd = os.getcwd()
        self.addCleanup(os.chdir, self._cwd)
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        os.chdir(self.repo)

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            capture_output=True, text=True, check=True,
        ).stdout

    def write(self, relpath, text="{}"):
        path = self.repo / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "--no-gpg-sign", "--no-verify", "-q", "-m", message)

    def publish_baseline(self):
        """A repo with one published collection, on branch `main`."""
        self.write("collections/README.md", "# Collections\n")
        self.write("collections/foda-1/archive.json")
        self.commit("publish foda-1")

    def test_publishing_a_new_collection_is_allowed(self):
        self.publish_baseline()
        self.write("collections/barnes-1/archive.json")
        self.commit("publish barnes-1")
        self.assertEqual(check_immutability("main~1"), [])

    # Mutation caught: reverting to the unconditional `continue` on status A,
    # which is what the gate did originally. A contributor could then add a
    # file under an already-published collection -- changing what that
    # collection is, and its digest -- and the gate would not flag it.
    def test_adding_a_file_to_a_published_collection_FAILS(self):
        self.publish_baseline()
        self.write("collections/foda-1/errata.json")
        self.commit("sneak a file into a published collection")
        with self.assertRaises(Failure) as caught:
            check_immutability("main~1")
        self.assertIn("collections/foda-1/errata.json", str(caught.exception))

    def test_editing_a_published_file_FAILS(self):
        self.publish_baseline()
        self.write("collections/foda-1/archive.json", '{"edited": true}')
        self.commit("edit a published archive")
        with self.assertRaises(Failure):
            check_immutability("main~1")

    def test_deleting_a_published_file_FAILS(self):
        self.publish_baseline()
        (self.repo / "collections/foda-1/archive.json").unlink()
        self.commit("delete a published archive")
        with self.assertRaises(Failure):
            check_immutability("main~1")

    # `collections/README.md` is repository furniture sitting directly in
    # collections/, not a published collection. A naive split("/")[1] reads it
    # as a collection named "README.md"; nothing then matches it, so the error
    # is silent rather than loud.
    def test_a_file_directly_in_collections_is_not_a_collection(self):
        self.publish_baseline()
        self.write("collections/CONTRIBUTING.md", "# How to contribute\n")
        self.commit("add repo furniture")
        self.assertEqual(check_immutability("main~1"), [])
