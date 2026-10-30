import pytest

from markly.app import VERSION_FILE, main, read_version


def test_read_version_from_project_file():
    assert read_version() == VERSION_FILE.read_text(encoding="utf-8").strip()


def test_read_version_strips_whitespace(tmp_path):
    path = tmp_path / ".version"
    path.write_text("  2.3.4\n", encoding="utf-8")
    assert read_version(path) == "2.3.4"


@pytest.mark.parametrize("content", [None, "", "\n  \n"])
def test_read_version_errors(tmp_path, content):
    path = tmp_path / ".version"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    with pytest.raises(RuntimeError):
        read_version(path)


def test_main_version(capsys):
    assert main(["markly", "--version"]) == 0
    assert capsys.readouterr().out == f"markly {read_version()}\n"


def test_main_version_missing_file(capsys, monkeypatch, tmp_path):
    monkeypatch.setattr("markly.app.VERSION_FILE", tmp_path / "manca")
    assert main(["markly", "--version"]) == 1
    assert "versione non disponibile" in capsys.readouterr().err
