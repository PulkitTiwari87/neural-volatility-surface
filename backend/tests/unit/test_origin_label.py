"""GR-DATA-04: ingest() records an explicit data origin; synthetic files can never be stored as real (SYNTHETIC data)."""
import json
import tempfile
import unittest
from pathlib import Path

from volatility_lab.api.service import RunStore
from volatility_lab.config.settings import Config
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.storage.raw_store import OverwriteError, ingest

CFG = Config()


class OriginLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        wide, _ = make_chain(10, seed=1)
        cls.src = cls.dir / "chain.csv"
        wide.to_csv(cls.src, index=False)
        cls.syn = cls.dir / "chain.synthetic.csv"
        wide.to_csv(cls.syn, index=False)
        cls.base = ingest(cls.dir / "base", [cls.src], CFG)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def _ds(self, store, m):
        return self.dir / store / "datasets" / m["version_id"]

    def test_origin_is_recorded_in_manifest_and_meta_json(self):
        m = ingest(self.dir / "s1", [self.src], CFG, origin="synthetic")
        self.assertEqual(m["origin"], "synthetic")
        d = self._ds("s1", m)
        self.assertEqual(json.loads((d / "manifest.json").read_text())["origin"], "synthetic")
        self.assertEqual(json.loads((d / "meta.json").read_text())["origin"], "synthetic")

    def test_version_id_is_unchanged_by_origin(self):
        syn = ingest(self.dir / "s2", [self.src], CFG, origin="synthetic")
        real = ingest(self.dir / "s3", [self.src], CFG, origin="real")
        self.assertEqual(syn["version_id"], self.base["version_id"])
        self.assertEqual(real["version_id"], self.base["version_id"])

    def test_origin_none_leaves_manifest_keys_identical_to_baseline(self):
        m = ingest(self.dir / "s4", [self.src], CFG)
        self.assertNotIn("origin", m)
        self.assertEqual(set(m), set(self.base))
        self.assertEqual((self._ds("s4", m) / "manifest.json").read_text(),
                         (self._ds("base", m) / "manifest.json").read_text())
        self.assertFalse((self._ds("s4", m) / "meta.json").exists())

    def test_invalid_origin_is_rejected_before_anything_is_stored(self):
        for bad in ("Synthetic", "", "fake", 1):
            with self.assertRaises(ValueError, msg=repr(bad)):
                ingest(self.dir / "s5", [self.src], CFG, origin=bad)
        self.assertFalse((self.dir / "s5").exists())

    def test_synthetic_named_file_cannot_be_stored_as_real(self):
        with self.assertRaises(ValueError):
            ingest(self.dir / "s6", [self.syn], CFG, origin="real")
        with self.assertRaises(ValueError):
            ingest(self.dir / "s6", [self.src, self.syn], CFG, origin="real")
        self.assertFalse((self.dir / "s6").exists())
        # the same file is fine when labelled synthetic (or unlabelled: nothing is refused)
        self.assertEqual(ingest(self.dir / "s6", [self.syn], CFG, origin="synthetic")["origin"], "synthetic")
        self.assertNotIn("origin", ingest(self.dir / "s7", [self.syn], CFG))

    def test_same_origin_twice_reuses_and_a_different_label_is_refused(self):
        root = self.dir / "s8"
        first = ingest(root, [self.src], CFG, origin="synthetic")
        second = ingest(root, [self.src], CFG, origin="synthetic")
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        self.assertEqual({**first, "reused": None}, {**second, "reused": None})
        with self.assertRaises(OverwriteError):
            ingest(root, [self.src], CFG, origin="real")

    def test_existing_meta_json_is_not_overwritten(self):
        root = self.dir / "s9"
        m = ingest(root, [self.src], CFG, origin="synthetic")
        meta = self._ds("s9", m) / "meta.json"
        meta.write_text(json.dumps({"origin": "synthetic", "description": "hand written"}))
        ingest(root, [self.src], CFG, origin="synthetic")
        self.assertEqual(json.loads(meta.read_text())["description"], "hand written")

    def test_api_uses_manifest_origin_when_meta_json_is_absent(self):
        m = ingest(self.dir / "s10", [self.src], CFG, origin="synthetic")
        d = self._ds("s10", m)
        (d / "meta.json").unlink()
        info = RunStore(d.parent).run_info(m["version_id"])
        self.assertEqual(info["origin"], "synthetic")
        self.assertNotIn("origin_conflict", info)

    def test_api_flags_conflicting_labels_and_reports_unlabelled(self):
        m = ingest(self.dir / "s11", [self.src], CFG, origin="synthetic")
        d = self._ds("s11", m)
        (d / "meta.json").write_text(json.dumps({"origin": "real", "description": "x"}))
        store = RunStore(d.parent)
        info = store.run_info(m["version_id"])
        self.assertEqual((info["origin"], info["origin_conflict"]), ("unlabelled", True))
        self.assertEqual(store.list_runs()[0]["origin"], "unlabelled")

    def test_api_unlabelled_run_without_either_label_stays_unlabelled(self):
        d = self._ds("base", self.base)
        info = RunStore(d.parent).run_info(self.base["version_id"])
        self.assertEqual(info["origin"], "unlabelled")
        self.assertNotIn("origin_conflict", info)


if __name__ == "__main__":
    unittest.main()
