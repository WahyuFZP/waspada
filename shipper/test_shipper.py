"""Uji pengirim log tanpa dependensi: python -m unittest -v (dari folder shipper)."""
import os
import tempfile
import unittest

from waspada_shipper import Follower, Rejected, send, to_records


class FollowerTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "auth.log")

    def tearDown(self):
        self.dir.cleanup()

    def follow(self):
        f = Follower(self.path)
        self.addCleanup(lambda: f.fh and f.fh.close())
        return f

    def write(self, text, mode="a"):
        with open(self.path, mode, encoding="utf-8", newline="") as fh:
            fh.write(text)

    def test_existing_file_starts_at_end(self):
        self.write("baris lama\n")
        f = self.follow()
        self.assertEqual(f.lines(), [])
        self.write("baris baru\n")
        self.assertEqual(f.lines(), ["baris baru"])

    def test_file_created_later_is_read_from_start(self):
        f = self.follow()
        self.assertEqual(f.lines(), [])
        self.write("a\nb\n")
        self.assertEqual(f.lines(), ["a", "b"])

    def test_partial_line_waits_for_newline(self):
        f = self.follow()
        self.write("Failed pass")
        self.assertEqual(f.lines(), [])
        self.write("word\n")
        self.assertEqual(f.lines(), ["Failed password"])

    def test_rotation_reads_rest_of_old_then_new_file(self):
        f = self.follow()
        self.write("1\n")
        self.assertEqual(f.lines(), ["1"])
        self.write("2\n")
        os.replace(self.path, self.path + ".1")  # logrotate: file lama diganti nama, file baru dibuat
        self.write("3\n", mode="w")
        self.assertEqual(f.lines(), ["2", "3"])

    def test_truncation_restarts_from_beginning(self):
        f = self.follow()
        self.write("panjang sekali\n")
        f.lines()
        self.write("x\n", mode="w")
        self.assertEqual(f.lines(), ["x"])


class RecordsTest(unittest.TestCase):
    def test_suricata_keeps_alerts_only_and_skips_bad_json(self):
        lines = ['{"event_type":"alert","src_ip":"1.2.3.4"}', '{"event_type":"flow"}', "bukan json"]
        self.assertEqual(to_records("suricata", lines), [{"event_type": "alert", "src_ip": "1.2.3.4", "kind": "suricata"}])

    def test_auth_wraps_lines(self):
        self.assertEqual(to_records("auth", ["x"]), [{"kind": "auth", "line": "x"}])


class SendTest(unittest.TestCase):
    def test_rejected_batch_is_retried_one_by_one(self):
        calls = []

        def fake_post(api, token, records):
            calls.append(len(records))
            return 422 if len(records) > 1 or records[0]["line"] == "rusak" else 200

        send("http://x", "t", [{"line": "a"}, {"line": "rusak"}, {"line": "b"}], post=fake_post)
        self.assertEqual(calls, [3, 1, 1, 1])

    def test_wrong_token_stops_and_server_error_retries(self):
        with self.assertRaises(Rejected):
            send("http://x", "t", [{}], post=lambda *_: 401)
        with self.assertRaises(OSError):
            send("http://x", "t", [{}], post=lambda *_: 503)


if __name__ == "__main__":
    unittest.main()
