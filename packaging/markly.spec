# PyInstaller: pyinstaller packaging/markly.spec  ->  dist/markly/markly
from pathlib import Path, PurePosixPath

from PyInstaller.depend.bindepend import get_imports

root = Path(SPECPATH).parent

a = Analysis(
    [str(root / "packaging" / "launcher.py")],
    pathex=[str(root)],
    datas=[
        (str(root / "markly" / "style.css"), "markly"),
        (str(root / ".version"), "."),
    ],
    hiddenimports=["linkify_it", "pygments.lexers", "pygments.formatters.html"],
    # Moduli che un ambiente con --system-site-packages può far entrare nel bundle.
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide6.QtMultimedia", "numpy", "PIL", "psutil", "gi"],
)

# --- Snellimento: markly usa solo QtWidgets + QtWebEngine e non usa QML. ---

QT = "PySide6/Qt/"
# Plugin Qt utili a una finestra desktop su X11 o Wayland; il resto non serve.
KEEP_PLUGIN_DIRS = {
    "platforms", "platforminputcontexts", "platformthemes", "xcbglintegrations",
    "wayland-shell-integration", "wayland-graphics-integration-client",
    "wayland-decoration-client", "iconengines", "imageformats",
}
DROP_PLUGINS = {
    "libqgtk3.so",  # tema GTK: porterebbe con sé tutta GTK 3
    "libqtvirtualkeyboardplugin.so", "libqvnc.so", "libqlinuxfb.so", "libqeglfs.so",
    "libqminimal.so", "libqminimalegl.so", "libqvkkhrdisplay.so",
}
# Traduzioni: solo italiano e inglese.
KEEP_LOCALES = {"it.pak", "en-US.pak"}


def keep_file(dest):
    path = PurePosixPath(dest)
    if dest.startswith(QT + "qml/"):
        return False
    if dest.startswith(QT + "plugins/"):
        return path.parts[3] in KEEP_PLUGIN_DIRS and path.name not in DROP_PLUGINS
    if dest.startswith(QT + "translations/qtwebengine_locales/"):
        return path.name in KEEP_LOCALES
    if dest.startswith(QT + "translations/"):
        return path.stem.endswith(("_it", "_en"))
    return path.name != "qtwebengine_devtools_resources.pak"


def is_plain_library(dest):
    # Librerie condivise da tenere solo se qualche altro binario le usa.
    return "/" not in dest or dest.startswith(QT + "lib/")


binaries = [b for b in a.binaries if keep_file(b[0])]

# Tiene le librerie raggiungibili, tramite le dipendenze dichiarate, dai binari principali:
# moduli di estensione, plugin, QtWebEngineProcess e libpython (caricata dal bootloader).
libraries = {PurePosixPath(d).name: (d, s) for d, s, _ in binaries if is_plain_library(d)}
todo = [s for d, s, _ in binaries if not is_plain_library(d) or d.startswith("libpython")]
needed = set()
while todo:
    for name, _ in get_imports(todo.pop()):
        name = PurePosixPath(name).name
        if name in libraries and name not in needed:
            needed.add(name)
            todo.append(libraries[name][1])

a.binaries = [
    b for b in binaries
    if not is_plain_library(b[0]) or PurePosixPath(b[0]).name in needed or b[0].startswith("libpython")
]
kept = {b[0] for b in a.binaries}
a.datas = [
    d for d in a.datas
    if keep_file(d[0]) and (d[2] != "SYMLINK" or d[1] in kept)
]

pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="markly", console=False)
coll = COLLECT(exe, a.binaries, a.datas, name="markly")
