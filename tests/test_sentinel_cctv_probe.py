import argparse
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tools import sentinel_cctv_probe as probe


class SentinelProbeTests(unittest.TestCase):
    def test_normalized_base_url_trims_trailing_slash(self):
        self.assertEqual(
            probe.normalized_base_url(" https://live.sentinelgujarat.in/ "),
            "https://live.sentinelgujarat.in",
        )

    def test_normalized_base_url_rejects_empty_value(self):
        with self.assertRaises(probe.ProbeError):
            probe.normalized_base_url("   ")

    def test_url_join_handles_relative_absolute_and_external_urls(self):
        base_url = "https://live.sentinelgujarat.in"
        self.assertEqual(
            probe.url_join(base_url, "/stream/13"),
            "https://live.sentinelgujarat.in/stream/13",
        )
        self.assertEqual(
            probe.url_join(base_url, "api/cameras"),
            "https://live.sentinelgujarat.in/api/cameras",
        )
        self.assertEqual(
            probe.url_join(base_url, "https://example.test/feed.m3u8"),
            "https://example.test/feed.m3u8",
        )

    def test_parse_camera_ids_uses_defaults_env_and_explicit_values(self):
        with mock.patch.dict(probe.os.environ, {}, clear=True):
            self.assertEqual(probe.parse_camera_ids(None), ["1", "6", "13", "22"])

        with mock.patch.dict(probe.os.environ, {"SENTINEL_PROBE_CAMERA_IDS": "2, 4,,8"}):
            self.assertEqual(probe.parse_camera_ids(None), ["2", "4", "8"])

        self.assertEqual(probe.parse_camera_ids("9,10"), ["9", "10"])

        with self.assertRaises(probe.ProbeError):
            probe.parse_camera_ids(" , ")

    def test_summarize_cameras_counts_formats_and_preserves_samples(self):
        cameras = [
            {
                "id": 1,
                "number": "CAM-001",
                "name": "Bridge",
                "location": "Ahmedabad",
                "status": "live",
                "codec": "h264",
                "container": "mp4",
                "delivery": "progressive",
            },
            {
                "id": 6,
                "number": "CAM-006",
                "name": "Road",
                "location": "Gandhinagar",
                "status": "offline",
                "codec": "avi",
                "container": "avi",
                "delivery": "progressive",
            },
            {
                "id": 13,
                "status": "live",
                "codec": "h264",
                "container": "mkv",
                "delivery": "hls",
            },
        ]

        summary = probe.summarize_cameras(cameras)

        self.assertEqual(summary["camera_count"], 3)
        self.assertEqual(summary["status"], {"live": 2, "offline": 1})
        self.assertEqual(summary["codec"], {"avi": 1, "h264": 2})
        self.assertEqual(summary["container"], {"avi": 1, "mkv": 1, "mp4": 1})
        self.assertEqual(summary["delivery"], {"hls": 1, "progressive": 2})
        self.assertEqual(summary["camera_ids"], ["1", "6", "13"])
        self.assertEqual(summary["sample_locations"][0]["location"], "Ahmedabad")

    def test_stream_url_from_state_prefers_hls_then_progressive(self):
        base_url = "https://live.sentinelgujarat.in"

        self.assertEqual(
            probe.stream_url_from_state(
                base_url,
                {"hls_url": "/hls/1/index.m3u8", "stream_url": "/stream/1"},
            ),
            ("hls", "https://live.sentinelgujarat.in/hls/1/index.m3u8"),
        )
        self.assertEqual(
            probe.stream_url_from_state(base_url, {"stream_url": "/stream/13"}),
            ("progressive", "https://live.sentinelgujarat.in/stream/13"),
        )
        self.assertEqual(probe.stream_url_from_state(base_url, {}), (None, None))

    def test_ffprobe_stream_reports_successful_metadata(self):
        completed = subprocess.CompletedProcess(
            args=["ffprobe"],
            returncode=0,
            stdout=json.dumps(
                {
                    "streams": [{"index": 0, "codec_name": "h264", "codec_type": "video"}],
                    "format": {"format_name": "mov,mp4,m4a,3gp,3g2,mj2"},
                }
            ),
            stderr="",
        )

        with mock.patch.object(probe.shutil, "which", return_value="ffprobe"):
            with mock.patch.object(probe.subprocess, "run", return_value=completed) as run:
                result = probe.ffprobe_stream("https://example.test/stream/1", 3)

        self.assertTrue(result["ok"])
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["probe"]["streams"][0]["codec_name"], "h264")
        self.assertIn("-show_entries", run.call_args.args[0])
        self.assertIn("https://example.test/stream/1", run.call_args.args[0])

    def test_ffprobe_stream_reports_nonzero_status_without_raising(self):
        completed = subprocess.CompletedProcess(
            args=["ffprobe"],
            returncode=1,
            stdout="",
            stderr="Server returned 5XX Server Error reply",
        )

        with mock.patch.object(probe.shutil, "which", return_value="ffprobe"):
            with mock.patch.object(probe.subprocess, "run", return_value=completed):
                result = probe.ffprobe_stream("https://example.test/stream/6", 2)

        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 1)
        self.assertIn("5XX", result["stderr"])

    def test_ffprobe_stream_reports_timeout_without_raising(self):
        with mock.patch.object(probe.shutil, "which", return_value="ffprobe"):
            with mock.patch.object(
                probe.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(cmd=["ffprobe"], timeout=1),
            ):
                result = probe.ffprobe_stream("https://example.test/stream/22", 1)

        self.assertFalse(result["ok"])
        self.assertIsNone(result["returncode"])
        self.assertIn("timed out", result["error"])

    def test_ffprobe_stream_requires_ffprobe_on_path(self):
        with mock.patch.object(probe.shutil, "which", return_value=None):
            with self.assertRaises(probe.ProbeError):
                probe.ffprobe_stream("https://example.test/stream/1", 1)

    def test_cmd_stream_test_skips_offline_camera_without_ffprobe(self):
        args = argparse.Namespace(
            base_url="https://live.sentinelgujarat.in",
            camera_id="99",
            http_timeout=1,
            ffprobe_timeout=1,
        )

        with mock.patch.object(
            probe,
            "fetch_camera_state",
            return_value={"id": 99, "status": "offline", "stream_url": "/stream/99"},
        ):
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = probe.cmd_stream_test(args)

        payload = json.loads(output.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["message"], "Camera is not live; stream probe skipped.")

    def test_write_json_creates_parent_directories_and_sorted_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "nested" / "payload.json"
            probe.write_json(output_path, {"b": 2, "a": 1})

            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                '{\n  "a": 1,\n  "b": 2\n}\n',
            )


if __name__ == "__main__":
    unittest.main()
