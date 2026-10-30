"""Finestra principale e punto di ingresso dell'applicazione."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView

from .renderer import MARKDOWN_EXTENSIONS, DocumentError, read_text, render_page
from .security import ReaderPage, create_profile, register_scheme

APP_NAME = "markly"
# Nel sorgente è la radice del progetto; nel bundle PyInstaller è la cartella _internal.
VERSION_FILE = Path(__file__).resolve().parent.parent / ".version"
_FILE_FILTER = (
    "Documenti Markdown ("
    + " ".join(f"*{ext}" for ext in MARKDOWN_EXTENSIONS)
    + ");;Tutti i file (*)"
)


class ReaderView(QWebEngineView):
    clicked = Signal()

    def event(self, event: QEvent) -> bool:
        # I clic arrivano al widget interno creato da WebEngine, non alla vista.
        if event.type() == QEvent.Type.ChildAdded and isinstance(event.child(), QWidget):
            event.child().installEventFilter(self)
        return super().event(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress:
            self.clicked.emit()
        return super().eventFilter(watched, event)

    def contextMenuEvent(self, event) -> None:
        # Menu contestuale ridotto alle sole azioni di lettura.
        menu = QMenu(self)
        menu.addAction(self.pageAction(QWebEnginePage.WebAction.Copy))
        menu.addAction(self.pageAction(QWebEnginePage.WebAction.SelectAll))
        menu.exec(event.globalPos())


class FindBar(QWidget):
    """Barra di ricerca nel documento: Invio cerca avanti, Maiusc+Invio indietro."""

    def __init__(self, page: QWebEnginePage, parent=None) -> None:
        super().__init__(parent)
        self._page = page
        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText("Cerca nel documento")
        self._edit.setClearButtonEnabled(True)
        self._edit.textChanged.connect(lambda _text: self.find())
        self._edit.returnPressed.connect(self._on_return)
        self._matches = QLabel(self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.addWidget(self._edit, 1)
        layout.addWidget(self._matches)
        page.findTextFinished.connect(self._show_result)
        # Attiva solo mentre la barra è visibile.
        shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        shortcut.activated.connect(self.close_bar)
        self.hide()

    def open_bar(self) -> None:
        self.show()
        self._edit.setFocus()
        self._edit.selectAll()
        if self._edit.text():
            self.find()

    def close_bar(self) -> None:
        if self.isVisible():
            self.hide()
            self._page.findText("")  # rimuove l'evidenziazione
            self._matches.clear()

    def find(self, backward: bool = False) -> None:
        flags = QWebEnginePage.FindFlag(0)
        if backward:
            flags |= QWebEnginePage.FindFlag.FindBackward
        self._page.findText(self._edit.text(), flags)

    def _on_return(self) -> None:
        backward = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
        self.find(backward)

    def _show_result(self, result) -> None:
        if not self._edit.text():
            self._matches.clear()
        elif result.numberOfMatches():
            self._matches.setText(f"{result.activeMatch()} di {result.numberOfMatches()}")
        else:
            self._matches.setText("Nessun risultato")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._path: Path | None = None
        self._last_dir = str(Path.home())

        # Il profilo deve sopravvivere alla pagina: appartiene all'applicazione.
        profile, self._handler, self._interceptor = create_profile(QApplication.instance())
        self._page = ReaderPage(profile, self)
        self._page.open_document.connect(self.open_file)
        self._view = ReaderView(self)
        self._view.setPage(self._page)
        self._view.setHtml(
            "<html><body style='font-family:sans-serif;color:#888;text-align:center;"
            "padding-top:20%'>Apri un file Markdown con Ctrl+O</body></html>"
        )
        self._find_bar = FindBar(self._page, self)
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._view, 1)
        layout.addWidget(self._find_bar)
        self.setCentralWidget(central)
        self._view.clicked.connect(self._find_bar.close_bar)

        # Ricerca: solo da tastiera, senza voce di menu.
        find_action = QAction(self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self._find_bar.open_bar)
        self.addAction(find_action)

        open_action = QAction("&Apri…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.choose_file)
        quit_action = QAction("&Esci", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        about_action = QAction("&Informazioni su markly", self)
        about_action.triggered.connect(self.show_about)
        help_menu = self.menuBar().addMenu("&Aiuto")
        help_menu.addAction(about_action)

        self.resize(980, 1000)
        self._update_title()

    def choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri documento Markdown", self._last_dir, _FILE_FILTER
        )
        if path:
            self.open_file(Path(path))

    def open_file(self, path: Path) -> bool:
        """Apre e mostra un documento; in caso di errore resta quello precedente."""
        path = path.expanduser().resolve()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            page = render_page(read_text(path), path.name)
        except DocumentError as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Impossibile aprire il file", str(exc))
            return False
        QApplication.restoreOverrideCursor()
        self._handler.set_document(path, page)
        self._page.show_document(path)
        self._path = path
        self._last_dir = str(path.parent)
        self._find_bar.close_bar()
        self._update_title()
        return True

    def show_about(self) -> None:
        try:
            version = read_version()
        except RuntimeError:
            version = "non disponibile"
        QMessageBox.about(
            self,
            f"Informazioni su {APP_NAME}",
            f"<h3>{APP_NAME}</h3>"
            f"<p>Versione {version}</p>"
            "<p>Lettore Markdown per Linux.</p>"
            "<p>© 2026 Gabriele Murara<br>Licenza MIT</p>",
        )

    def _update_title(self) -> None:
        self.setWindowTitle(f"{self._path.name} — {APP_NAME}" if self._path else APP_NAME)


def read_version(path: Path | None = None) -> str:
    """Restituisce la versione dell'applicazione letta dal file .version."""
    path = VERSION_FILE if path is None else path
    try:
        version = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"impossibile leggere «{path}»: {exc.strerror or exc}") from None
    if not version:
        raise RuntimeError(f"il file «{path}» è vuoto")
    return version


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    parser = argparse.ArgumentParser(prog="markly", description="Lettore Markdown.")
    parser.add_argument("file", nargs="?", help="documento Markdown da aprire")
    parser.add_argument("--version", action="store_true", help="mostra la versione ed esce")
    args, qt_args = parser.parse_known_args(argv[1:])

    if args.version:
        try:
            print(f"{parser.prog} {read_version()}")
        except RuntimeError as exc:
            print(f"{parser.prog}: versione non disponibile: {exc}", file=sys.stderr)
            return 1
        return 0

    register_scheme()
    app = QApplication([argv[0], *qt_args])
    app.setApplicationName(APP_NAME)
    app.setDesktopFileName("markly")
    window = MainWindow()
    window.show()
    if args.file:
        window.open_file(Path(args.file))
    status = app.exec()
    del window  # distrugge la pagina prima del profilo
    return status
