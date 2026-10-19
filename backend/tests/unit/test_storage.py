"""Phase 1 acceptance: write-once raw store, deterministic dataset versions, conserved ledgers (SYNTHETIC data)."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from volatility_lab.config.settings import Config, DataConfig
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.storage.raw_store import OverwriteError, RawStore, ingest, panel_sha256

CFG = Config()


def _write_chain(path: Path, seed: int) -> Path:
    wide, _ = make_chain(10, seed=seed)
    wide.to_csv(path, index=False)
    return path


class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        cls.src = _write_chain(cls.dir / "chain.csv", seed=1)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_same_inputs_twice_give_same_version_and_identical_manifest(self):
        root = self.dir / "store_a"
        first = ingest(root, [self.src], CFG)
        second = ingest(root, [self.src], CFG)
        self.assertFalse(first["reused"])
        self.assertTrue(second["reused"])
        self.assertEqual(first["version_id"], second["version_id"])
        self.assertEqual({**first, "reused": None}, {**second, "reused": None})

    def test_ledgers_are_conserved_and_recorded(self):
        m = ingest(self.dir / "store_b", [self.src], CFG)
        for key in ("ledger_prefilter", "ledger_quotes"):
            led = m[key]
            self.assertEqual(led["rows_in"], led["kept"] + sum(led["rejects"].values()))
        self.assertTrue(m["ledgers_conserved"])

    def test_changed_bytes_or_config_make_a_new_version(self):
        root = self.dir / "store_c"
        base = ingest(root, [self.src], CFG)
        other = ingest(root, [_write_chain(self.dir / "chain2.csv", seed=2)], CFG)
        self.assertNotEqual(base["version_id"], other["version_id"])
        cfg2 = Config(data=DataConfig(min_dte=3))
        self.assertNotEqual(base["version_id"], ingest(root, [self.src], cfg2)["version_id"])

    def test_existing_dataset_with_different_content_is_refused(self):
        root = self.dir / "store_d"
        m = ingest(root, [self.src], CFG)
        mf = root / "datasets" / m["version_id"] / "manifest.json"
        mf.write_text(mf.read_text().replace('"schema"', '"schema_x"'))
        with self.assertRaises(OverwriteError):
            ingest(root, [self.src], CFG)

    def test_raw_objects_are_content_addressed_and_cannot_be_altered(self):
        store = RawStore(self.dir / "store_e")
        a = store.put(self.src)
        self.assertEqual(a, store.put(self.src))          # idempotent
        self.assertEqual(store.verify(), [])
        Path(a["stored"]).write_bytes(b"corrupt")
        self.assertTrue(any("hash mismatch" in p for p in store.verify()))
        with self.assertRaises(OverwriteError):
            store.put(self.src)

    def test_panel_hash_is_stable_and_sensitive(self):
        m = ingest(self.dir / "store_f", [self.src], CFG)
        with np.load(self.dir / "store_f" / "datasets" / m["version_id"] / "panel.npz") as z:
            panel = {k: z[k] for k in z.files}
        self.assertEqual(panel_sha256(panel), m["panel_sha256"])
        changed = {**panel, "iv": panel["iv"].copy()}
        i = np.argwhere(np.isfinite(changed["iv"]))[0]
        changed["iv"][tuple(i)] += 1e-9
        self.assertNotEqual(panel_sha256(changed), m["panel_sha256"])

    def test_manifest_is_valid_json_with_inputs_and_config(self):
        m = ingest(self.dir / "store_g", [self.src], CFG)
        back = json.loads((self.dir / "store_g" / "datasets" / m["version_id"] / "manifest.json").read_text())
        self.assertEqual(back["config_sha256"], CFG.sha256())
        self.assertEqual(back["inputs"][0]["name"], "chain.csv")


if __name__ == "__main__":
    unittest.main()
