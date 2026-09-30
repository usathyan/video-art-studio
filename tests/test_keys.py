import importlib
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


def _fresh(monkeypatch, tmp_path, env=None):
    """Reload common/keys with HOME pointed at tmp_path and a controlled environment."""
    monkeypatch.setenv("HOME", str(tmp_path))
    for n in (
        "OPENROUTER_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "ELEVENLABS_API_KEY",
        "ELEVEN_API",
    ):
        monkeypatch.delenv(n, raising=False)
    for k, v in (env or {}).items():
        monkeypatch.setenv(k, v)
    import keys

    import common

    importlib.reload(common)
    return common, importlib.reload(keys)


def test_keys_file_is_private_and_wins_over_shell(monkeypatch, tmp_path):
    f = tmp_path / ".config" / "video-art" / ".env"
    f.parent.mkdir(parents=True)
    f.write_text("OPENROUTER_API_KEY=from-file\n")
    common, _ = _fresh(
        monkeypatch, tmp_path, {"OPENROUTER_API_KEY": "from-shell", "GEMINI_API_KEY": "g-shell"}
    )
    assert common.key("openrouter") == "from-file"  # the file wins
    assert common.key("gemini") == "g-shell"  # shell fills gaps


def test_ensure_creates_template_with_600(monkeypatch, tmp_path):
    _, keys = _fresh(monkeypatch, tmp_path)
    f = keys.ensure()
    assert stat.S_IMODE(os.stat(f).st_mode) == 0o600
    assert stat.S_IMODE(os.stat(f.parent).st_mode) == 0o700
    assert "OPENROUTER_API_KEY=" in f.read_text()


def test_import_copies_shell_keys_under_standard_names(monkeypatch, tmp_path):
    _, keys = _fresh(
        monkeypatch, tmp_path, {"OPENROUTER_API_KEY": "sk-or-abc", "ELEVEN_API": "sk_legacy_name"}
    )
    keys.ensure()
    keys.import_from_shell()
    text = keys.KEYS_FILE.read_text()
    assert "OPENROUTER_API_KEY=sk-or-abc" in text
    assert "ELEVENLABS_API_KEY=sk_legacy_name" in text  # legacy shell name → standard file name
    assert keys.mask("sk-or-v1-0123456789abcdef") == "sk-or-…cdef"


def test_comment_after_empty_value_is_not_a_key(monkeypatch, tmp_path):
    f = tmp_path / ".config" / "video-art" / ".env"
    f.parent.mkdir(parents=True)
    f.write_text("ELEVENLABS_API_KEY=              # optional\n")
    _fresh(monkeypatch, tmp_path)
    assert "ELEVENLABS_API_KEY" not in os.environ
