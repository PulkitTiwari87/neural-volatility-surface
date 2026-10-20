"""Raw-store atomicity (AP-004 Patch 2, finding C-04). SYNTHETIC inputs and temp directories only.

* an interrupted copy must never leave an object that carries its hash name (a retry would otherwise be refused forever);
* a source that changes between hashing and copying is refused;
* a dataset directory left behind by an interrupted ingest (the manifest is written last) must not block a retry;
* the existing immutability semantics are unchanged: identical bytes are idempotent, a stored object that no longer
  matches its hash is refused, and a completed dataset whose manifest differs is never overwritten.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from volatility_lab.config.settings import Config
from volatility_lab.datasets.synthetic import make_chain
from volatility_lab.storage import raw_store
from volatility_lab.storage.raw_store import (OverwriteError, RawStore, dataset_version_id, ingest, sha256_file,
                                              verify_dataset)

_REAL_COPY = shutil.copyfile


def _half_then_fail(src, dst):
    data = Path(src).read_bytes()
    Path(dst).write_bytes(data[: len(data) // 2])
    raise OSError("simulated crash mid-copy")


def _copy_then_grow(src, dst):
    _REAL_COPY(src, dst)
    with open(dst, "ab") as fh:        # the source "changed" after it was hashed
        fh.write(b"x")


class PutAtomicityTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.dir = Path(self.td.name)
        self.src = self.dir / "a.csv"
        self.src.write_text("date,x\n" + "\n".join(f"{i},{i * 7 % 13}" for i in range(400)))
        self.digest = sha256_file(self.src)
        self.store = RawStore(self.dir / "store")
        self.dest = self.dir / "store" / "raw" / self.digest[:2] / f"{self.digest}.csv"

    def tearDown(self):
        self.td.cleanup()

    def test_interrupted_copy_leaves_no_object_under_its_hash_name_and_a_retry_succeeds(self):
        with mock.patch.object(raw_store.shutil, "copyfile", _half_then_fail):
            with self.assertRaises(OSError):
                self.store.put(self.src)
        self.assertFalse(self.dest.exists(), "a half-written file must not carry the object's hash name")
        self.assertTrue(self.store.verify(), "the leftover must stay visible to verify(), not silently disappear")
        info = self.store.put(self.src)                      # the real copy: the retry must not be refused
        self.assertEqual(info["sha256"], self.digest)
        self.assertEqual(sha256_file(self.dest), self.digest)
        self.assertEqual(self.store.verify(), [])

    def test_source_changing_between_hash_and_copy_is_refused_and_not_stored(self):
        with mock.patch.object(raw_store.shutil, "copyfile", _copy_then_grow):
            with self.assertRaises(OverwriteError):
                self.store.put(self.src)
        self.assertFalse(self.dest.exists())
        self.assertEqual(list((self.dir / "store" / "raw").rglob("*.part")), [], "the rejected temp file is removed")
        self.assertEqual(self.store.put(self.src)["sha256"], self.digest)

    def test_existing_semantics_unchanged_idempotent_put_and_corrupted_object_refused(self):
        first = self.store.put(self.src)
        second = self.store.put(self.src)
        self.assertEqual(first["sha256"], second["sha256"])
        self.dest.write_bytes(b"corrupted")
        with self.assertRaises(OverwriteError):
            self.store.put(self.src)


class IngestInterruptedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.td.name)
        wide, _ = make_chain(10, seed=1)
        cls.src = cls.dir / "chain.csv"
        wide.to_csv(cls.src, index=False)
        cls.cfg = Config()
        cls.vid = dataset_version_id([sha256_file(cls.src)], cls.cfg.sha256())

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_directory_left_by_an_interrupted_ingest_does_not_block_a_retry(self):
        root = self.dir / "interrupted"
        stale = root / "datasets" / self.vid
        stale.mkdir(parents=True)
        (stale / "panel.npz").write_bytes(b"half-written junk")        # crashed before the manifest was written
        m = ingest(root, [self.src], self.cfg)
        self.assertEqual(m["version_id"], self.vid)
        self.assertFalse(m["reused"])
        self.assertTrue((stale / "manifest.json").is_file())
        self.assertEqual(verify_dataset(root, self.vid), [], "the junk panel was replaced by the real one")
        self.assertTrue(ingest(root, [self.src], self.cfg)["reused"])

    def test_completed_dataset_is_still_never_overwritten(self):
        root = self.dir / "complete"
        ingest(root, [self.src], self.cfg)
        mf = root / "datasets" / self.vid / "manifest.json"
        doc = json.loads(mf.read_text())
        doc["surface_status_counts"] = {"tampered": 1}
        mf.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str))
        with self.assertRaises(OverwriteError):
            ingest(root, [self.src], self.cfg)


if __name__ == "__main__":
    unittest.main()
