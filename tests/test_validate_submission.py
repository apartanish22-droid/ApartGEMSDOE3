import tempfile
import unittest
from pathlib import Path

try:
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from scripts.validate_submission import check_submission
except ImportError as exc:  # pragma: no cover - depends on optional test environment
    raise unittest.SkipTest(f"rasterio/numpy required for GeoTIFF tests: {exc}")


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.template = self.root / "template.tif"
        self.candidate = self.root / "candidate.tif"
        self.transform = from_origin(500000, 4500000, 100, 100)
        self._write(
            self.template,
            np.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, -9999, -9999]], dtype="float32"),
            nodata=-9999,
        )
        self._write_candidate(np.array([[0, .2, .4, 1], [.1, .3, .5, .9], [.2, .8, np.nan, np.nan]], dtype="float32"), nodata=np.nan)

    def tearDown(self):
        self.tempdir.cleanup()

    def _write(self, path, values, nodata=None, transform=None, count=None):
        values = np.asarray(values)
        if values.ndim == 2:
            values = values[np.newaxis, :, :]
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            width=values.shape[2],
            height=values.shape[1],
            count=count or values.shape[0],
            dtype=values.dtype,
            crs="EPSG:32611",
            transform=transform or self.transform,
            nodata=nodata,
        ) as dst:
            dst.write(values)

    def _write_candidate(self, values, nodata=None, transform=None, dtype="float32"):
        self._write(
            self.candidate,
            np.asarray(values, dtype=dtype),
            nodata=nodata,
            transform=transform,
        )

    def test_valid_template_aligned_candidate_passes_format_only(self):
        report = check_submission(self.candidate, self.template)
        self.assertTrue(report["format_pass"])
        self.assertFalse(report["submission_authorized"])
        self.assertEqual(report["status"], "PASS_FORMAT_ONLY")
        self.assertEqual(report["raster"]["footprint_pixels"], 10)

    def test_nan_outside_footprint_without_nodata_is_accepted(self):
        values = np.array([[0, .2, .4, 1], [.1, .3, .5, .9], [.2, .8, np.nan, np.nan]], dtype="float32")
        self._write_candidate(values, nodata=None)
        report = check_submission(self.candidate, self.template)
        self.assertTrue(report["format_pass"])
        self.assertTrue(report["checks"]["outside_is_null_or_nan"])

    def test_in_footprint_value_above_one_fails(self):
        values = np.array([[0, .2, .4, 1], [.1, .3, 1.01, .9], [.2, .8, np.nan, np.nan]], dtype="float32")
        self._write_candidate(values, nodata=np.nan)
        report = check_submission(self.candidate, self.template)
        self.assertFalse(report["format_pass"])
        self.assertFalse(report["checks"]["inside_values_in_0_1"])

    def test_in_footprint_nan_fails(self):
        values = np.array([[0, .2, .4, 1], [.1, np.nan, .5, .9], [.2, .8, 0, 0]], dtype="float32")
        self._write_candidate(values, nodata=np.nan)
        report = check_submission(self.candidate, self.template)
        self.assertFalse(report["format_pass"])
        self.assertFalse(report["checks"]["no_nan_inside_footprint"])

    def test_finite_outside_footprint_without_nodata_fails(self):
        values = np.array([[0, .2, .4, 1], [.1, .3, .5, .9], [.2, .8, .01, .02]], dtype="float32")
        self._write_candidate(values)
        report = check_submission(self.candidate, self.template)
        self.assertFalse(report["format_pass"])
        self.assertFalse(report["checks"]["outside_is_null_or_nan"])

    def test_shifted_transform_fails(self):
        self._write_candidate(
            np.array([[0, .2, .4, 1], [.1, .3, .5, .9], [.2, .8, np.nan, np.nan]], dtype="float32"),
            nodata=np.nan,
            transform=from_origin(500100, 4500000, 100, 100),
        )
        report = check_submission(self.candidate, self.template)
        self.assertFalse(report["format_pass"])
        self.assertFalse(report["checks"]["transform_matches"])

    def test_wrong_dtype_fails(self):
        values = np.array([[0, .2, .4, 1], [.1, .3, .5, .9], [.2, .8, np.nan, np.nan]], dtype="float64")
        self._write_candidate(values, nodata=np.nan, dtype="float64")
        report = check_submission(self.candidate, self.template)
        self.assertFalse(report["format_pass"])
        self.assertFalse(report["checks"]["float32"])


if __name__ == "__main__":
    unittest.main()
