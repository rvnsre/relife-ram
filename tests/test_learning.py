"""Offline regression tests for the actual desktop and MCP learning logic."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "overlay/usr/local/lib/relife"
# Import the installed-layout module by its real name.
sys.path.insert(0, str(SOURCE))
import learning


class EducationTest(unittest.TestCase):
    def test_lesson_catalog(self):
        catalog = learning.lessons()
        self.assertEqual(len(catalog), len({lesson["id"] for lesson in catalog}))
        for lesson in catalog:
            self.assertTrue(all(lesson[key] for key in ("text", "question", "answer", "explanation")))

    def test_old_flashcard_export(self):
        card, = learning.parse_cards('[{"q":"2 + 2?","a":"4","due":0,"interval":0}]')
        learning.schedule(card, True, 1000)
        self.assertEqual(card["due"], 1000 + learning.DAY_MS)
        learning.schedule(card, False, 1000)
        self.assertEqual(card["due"], 61000)
        with self.assertRaises(ValueError):
            learning.parse_cards('[{"q":"q","a":"a","due":NaN,"interval":0}]')

    def test_science_and_lesson_duration(self):
        self.assertEqual(learning.calculate("Gərginlik (V)", "2 5"), 10)
        self.assertEqual(learning.calculate("Median", "5 4 1"), 4)
        self.assertAlmostEqual(learning.calculate("Torpağın nəmliyi (%)", "60 50"), 20)
        with self.assertRaises(ValueError):
            learning.calculate("Sürət (m/s)", "100 0")
        plan = learning.lesson_plan("Riyaziyyat", "7", "Kəsrlər", "Toplama", 47)
        self.assertEqual(sum(int(line.split()[0]) for line in plan.splitlines()[3:]), 47)

    def client(self, permissions, requests):
        args = [sys.executable, str(SOURCE / "mcp.py")]
        for tool in permissions:
            args.extend(["--allow", tool])
        run = subprocess.run(
            args, input="".join(json.dumps(message | {"jsonrpc": "2.0"}) + "\n" for message in requests),
            capture_output=True, text=True, check=True, timeout=3,
        )
        return {message["id"]: message for message in map(json.loads, run.stdout.splitlines())}

    def test_mcp_permissions_and_validation(self):
        requests = [
            {"id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
            {"method": "notifications/initialized"},
            {"id": 2, "method": "tools/list"},
            {"id": 3, "method": "tools/call", "params": {
                "name": "education.get_lesson", "arguments": {"id": "soil"}}},
            {"id": 4, "method": "tools/call", "params": {
                "name": "education.get_lesson", "arguments": {"id": "soil", "file": "/etc/passwd"}}},
        ]
        blocked = self.client([], requests)
        self.assertEqual(blocked[2]["result"]["tools"], [])
        self.assertIn("error", blocked[3])
        allowed = self.client(["education.get_lesson"], requests)
        self.assertEqual([tool["name"] for tool in allowed[2]["result"]["tools"]], ["education.get_lesson"])
        self.assertEqual(json.loads(allowed[3]["result"]["content"][0]["text"])["id"], "soil")
        self.assertIn("error", allowed[4])


if __name__ == "__main__":
    unittest.main()
