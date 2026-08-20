"""Focused tests for the signed publication boundary."""

import base64
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from publish_collections import (
    MANIFEST_PATH,
    PINNED_PUBLIC_KEY,
    PublicationFailure,
    _json_bytes,
    generate,
    sign_manifest,
    validate_manifest,
    validate_publishable_archive,
    verify_signature,
)


ROOT = pathlib.Path(__file__).parents[1]
SAMPLE = ROOT / "collections" / "foda-1-1"


class PublicationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def generate_sample(self, *, sign=False, public_key=PINNED_PUBLIC_KEY, key=None):
        collections = self.root / "collections"
        shutil.copytree(SAMPLE, collections / SAMPLE.name)
        output = self.root / "site"
        output.mkdir()
        shutil.copy(ROOT / "site" / "index.html", output / "index.html")
        shutil.copy(ROOT / "site" / "CNAME", output / "CNAME")
        return generate(
            collections,
            output,
            sign=sign,
            signing_key=key,
            public_key_base64=public_key,
        )

    def test_manifest_shape_and_artifact_measurements(self):
        result = self.generate_sample()
        manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifestSchema"], {"major": 1, "minor": 0})
        self.assertEqual(manifest["minReaderVersion"], "0.1.0")
        entry = manifest["collections"][0]
        archive = self.root / "site" / "collections" / "foda-1-1" / "archive.json"
        archive_bytes = archive.read_bytes()
        self.assertEqual(
            entry,
            {
                "id": "foda-1",
                "version": "1.0.0",
                "title": "Free and Open Dancing for All",
                "archiveUrl": (
                    "https://analect.callerscompendium.com/"
                    "collections/foda-1-1/archive.json"
                ),
                "archiveBytes": len(archive_bytes),
                "sha256": __import__("hashlib").sha256(archive_bytes).hexdigest(),
                "danceCount": 50,
                "license": "CC0-1.0",
                "permission": {
                    "grantor": "Isaac Banner",
                    "holder": "Isaac Banner",
                    "basis": "author",
                    "license": "CC0-1.0",
                    "fields": ["callingNotes", "walkthrough", "links"],
                },
                "requiredCapabilities": ["compositePhraseStructureV1"],
                "supersedes": None,
            },
        )

    def test_generation_is_deterministic(self):
        first = self.generate_sample()
        first_bytes = {
            path.relative_to(self.root / "site"): path.read_bytes()
            for path in (self.root / "site").rglob("*")
            if path.is_file()
        }
        other = pathlib.Path(self.tmp.name) / "other"
        shutil.copytree(SAMPLE, other / "collections" / SAMPLE.name)
        (other / "site").mkdir()
        generate(other / "collections", other / "site", sign=False)
        second_bytes = {
            path.relative_to(other / "site"): path.read_bytes()
            for path in (other / "site").rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            first_bytes[pathlib.Path("collections/manifest.json")],
            second_bytes[pathlib.Path("collections/manifest.json")],
        )
        self.assertEqual(
            first_bytes[pathlib.Path("collections/foda-1-1/archive.json")],
            second_bytes[pathlib.Path("collections/foda-1-1/archive.json")],
        )
        self.assertEqual(
            first["entries"][0]["archiveBytes"],
            len(first_bytes[pathlib.Path("collections/foda-1-1/archive.json")]),
        )

    def test_signature_verifies_and_wrong_key_is_refused(self):
        key = self.root / "ed25519.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
            check=True,
            capture_output=True,
        )
        public = __import__("publish_collections")._public_key_from_private(key)
        manifest = b'{"manifestSchema":{"major":1,"minor":0}}\n'
        signature = sign_manifest(
            manifest,
            key_path=key,
            public_key_base64=public,
        )
        self.assertTrue(verify_signature(manifest, signature, public))
        self.assertFalse(verify_signature(manifest + b"x", signature, public))
        encoded_signature = sign_manifest(
            manifest,
            key_b64=base64.b64encode(key.read_bytes()).decode("ascii"),
            public_key_base64=public,
        )
        self.assertTrue(verify_signature(manifest, encoded_signature, public))
        der = subprocess.run(
            ["openssl", "pkey", "-in", str(key), "-outform", "DER"],
            check=True,
            capture_output=True,
        ).stdout
        raw_seed_signature = sign_manifest(
            manifest,
            key_b64=base64.b64encode(der[-32:]).decode("ascii"),
            public_key_base64=public,
        )
        self.assertTrue(verify_signature(manifest, raw_seed_signature, public))
        with self.assertRaisesRegex(PublicationFailure, "signing credentials unavailable"):
            sign_manifest(manifest)
        self.assertNotEqual(public, PINNED_PUBLIC_KEY)

    def test_pages_artifact_contains_feed_and_static_site(self):
        key = self.root / "ed25519.pem"
        subprocess.run(
            ["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(key)],
            check=True,
            capture_output=True,
        )
        public = __import__("publish_collections")._public_key_from_private(key)
        result = self.generate_sample(sign=True, public_key=public, key=key)
        self.assertTrue((self.root / "site" / "CNAME").is_file())
        self.assertTrue((self.root / "site" / "index.html").is_file())
        self.assertTrue(result["manifest"].is_file())
        self.assertTrue(result["signature"].is_file())
        self.assertTrue(
            (self.root / "site" / "collections" / "foda-1-1" / "archive.json").is_file()
        )
        self.assertTrue(
            verify_signature(
                result["manifest"].read_bytes(),
                result["signature"].read_text(encoding="ascii"),
                public,
            )
        )

    def test_manifest_url_rules_are_enforced(self):
        result = self.generate_sample()
        manifest = json.loads(result["manifest"].read_text(encoding="utf-8"))
        manifest["collections"][0]["archiveUrl"] += "?cache=1"
        with self.assertRaisesRegex(PublicationFailure, "immutable allowed HTTPS URL"):
            validate_manifest(manifest, self.root / "site")

    def test_v1_rejection_guards(self):
        result = self.generate_sample()
        archive_path = self.root / "site" / "collections" / "foda-1-1" / "archive.json"
        base = json.loads(archive_path.read_text(encoding="utf-8"))
        mutations = {
            "programs": lambda value: value.__setitem__("programs", [{}]),
            "venues": lambda value: value.__setitem__("venues", [{}]),
            "published sources": lambda value: value.__setitem__("publishedSources", [{}]),
            "tags": lambda value: value.__setitem__("tags", [{}]),
            "top-level custom fields": lambda value: value.__setitem__("customFields", [{}]),
            "unknown top-level": lambda value: value.__setitem__("surprise", []),
            "dance custom fields": lambda value: value["dances"][0].__setitem__("customFields", [{}]),
            "source citations": lambda value: value["dances"][0].__setitem__("sourceCitations", [{}]),
            "published provenance": lambda value: value["dances"][0].__setitem__(
                "provenance", {"source": "publishedCollection"}
            ),
            "missing dance id": lambda value: value["dances"][0].pop("id"),
            "duplicate dance id": lambda value: value["dances"][1].__setitem__(
                "id", value["dances"][0]["id"]
            ),
            "unknown choreographer": lambda value: value["dances"][0]["authorIds"].__setitem__(
                0, "unknown"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                mutated = json.loads(json.dumps(base))
                mutate(mutated)
                with self.assertRaises(PublicationFailure):
                    validate_publishable_archive(mutated, name)

    def test_permission_coverage_and_custom_content_fail_before_generation(self):
        raw = json.loads((SAMPLE / "archive.json").read_text(encoding="utf-8"))
        for dance in raw["dances"]:
            dance.update(
                {
                    "hook": "",
                    "callingNotes": "",
                    "walkthrough": "",
                    "links": [],
                    "tunes": [],
                }
            )
        raw["dances"][0]["hook"] = "permission-sensitive prose"
        path = self.root / "archive.json"
        path.write_bytes(_json_bytes(raw))
        with self.assertRaisesRegex(PublicationFailure, "hook"):
            __import__("publish_collections")._sanitize_archive(raw, path, None)

        raw["dances"][0]["hook"] = ""
        raw["dances"][0]["customFields"] = [{"name": "private", "value": "do not drop"}]
        path.write_bytes(_json_bytes(raw))
        declaration = {"coversFields": ["customFields"]}
        with self.assertRaisesRegex(PublicationFailure, "custom-field content"):
            __import__("publish_collections")._sanitize_archive(raw, path, declaration)

    def test_supersedes_must_be_an_older_same_id_directory(self):
        collections = self.root / "collections"
        shutil.copytree(SAMPLE, collections / "foda-1-1")
        second = collections / "foda-1-2"
        shutil.copytree(SAMPLE, second)
        metadata = json.loads((second / "collection.json").read_text(encoding="utf-8"))
        metadata["version"] = "2"
        metadata["supersedes"] = "foda-1-1"
        (second / "collection.json").write_bytes(_json_bytes(metadata))
        output = self.root / "site"
        output.mkdir()
        generate(collections, output, sign=False)
        bad = json.loads((second / "collection.json").read_text(encoding="utf-8"))
        bad["supersedes"] = "other-1-1"
        (second / "collection.json").write_bytes(_json_bytes(bad))
        with self.assertRaisesRegex(PublicationFailure, "unknown collection"):
            generate(collections, self.root / "bad-site", sign=False)


if __name__ == "__main__":
    unittest.main()
