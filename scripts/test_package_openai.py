import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_openai import ROOT, build


class OpenAIPackageTest(unittest.TestCase):
    def test_package_isolated_from_cursor_and_shares_skill(self):
        with tempfile.TemporaryDirectory() as output:
            path = build(Path(output))
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                self.assertEqual(names, {
                    "soundlink/plugin.json", "soundlink/mcp.json", "soundlink/LICENSE",
                    "soundlink/assets/soundlink.png", "soundlink/skills/soundlink/SKILL.md",
                })
                self.assertEqual(archive.read("soundlink/skills/soundlink/SKILL.md"),
                                 (ROOT / "skills/soundlink/SKILL.md").read_bytes())
                mcp = json.loads(archive.read("soundlink/mcp.json"))
                server = mcp["mcpServers"]["soundlink"]
                self.assertNotIn("headers", server)
                self.assertEqual(server["extensions"]["com.openai"]["auth"]["client"],
                                 {"mode": "cimd"})
                for name in names:
                    if name.endswith((".json", ".md")):
                        self.assertNotIn(b"SOUNDLINK_API_KEY", archive.read(name))
            first = hashlib.sha256(path.read_bytes()).digest()
            self.assertEqual(first, hashlib.sha256(build(Path(output)).read_bytes()).digest())


if __name__ == "__main__":
    unittest.main()
