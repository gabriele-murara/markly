# PyInstaller: pyinstaller packaging/markly.spec  ->  dist/markly/markly
from pathlib import Path

root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "packaging" / "launcher.py")],
    pathex=[str(root)],
    datas=[
        (str(root / "markly" / "style.css"), "markly"),
        (str(root / ".version"), "."),
    ],
    hiddenimports=["linkify_it", "pygments.lexers", "pygments.formatters.html"],
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide6.QtMultimedia"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="markly", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="markly")
