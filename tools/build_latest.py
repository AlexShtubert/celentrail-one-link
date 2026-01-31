from pathlib import Path

Path("reports").mkdir(exist_ok=True)
(Path("reports") / "latest.md").write_text("# ok\n")

print("build_latest.py executed")
