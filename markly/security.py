"""Configurazione sicura di Qt WebEngine per la visualizzazione dei documenti.

Il documento viene servito dallo schema interno ``markly:`` (stesso percorso del
file sul disco), così link relativi, ancore e immagini locali funzionano senza
file temporanei. JavaScript è disattivato, ogni richiesta verso schemi diversi
da ``markly:``/``data:`` viene bloccata e i link esterni si aprono nel browser
di sistema invece che nella vista.
"""

from __future__ import annotations

import mimetypes
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineUrlRequestInfo,
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestJob,
    QWebEngineUrlScheme,
    QWebEngineUrlSchemeHandler,
)

from .renderer import MARKDOWN_EXTENSIONS

SCHEME = b"markly"
_ALLOWED_SCHEMES = {"markly", "data"}
_EXTERNAL_SCHEMES = {"http", "https", "mailto", "ftp"}


def register_scheme() -> None:
    """Da chiamare prima di creare la QApplication."""
    scheme = QWebEngineUrlScheme(SCHEME)
    scheme.setSyntax(QWebEngineUrlScheme.Syntax.Path)
    # Non "LocalScheme": con LocalContentCanAccessFileUrls disattivato le immagini
    # non verrebbero caricate; l'accesso ai file passa comunque solo dal gestore.
    scheme.setFlags(QWebEngineUrlScheme.Flag.SecureScheme)
    QWebEngineUrlScheme.registerScheme(scheme)


def to_view_url(path: Path) -> QUrl:
    url = QUrl.fromLocalFile(str(path))
    url.setScheme(SCHEME.decode())
    return url


def to_local_path(url: QUrl) -> Path:
    # toLocalFile() usa solo il percorso: frammento (#ancora) e query sono ignorati.
    local = QUrl(url)
    local.setScheme("file")
    return Path(local.toLocalFile())


def is_markdown(path: Path) -> bool:
    return path.suffix.lower() in MARKDOWN_EXTENSIONS


class DocumentSchemeHandler(QWebEngineUrlSchemeHandler):
    """Serve il documento renderizzato e le sole immagini locali che referenzia."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path: Path | None = None
        self._html = b""

    def set_document(self, path: Path, html: str) -> None:
        self._path = path
        self._html = html.encode("utf-8")

    def requestStarted(self, job: QWebEngineUrlRequestJob) -> None:
        path = to_local_path(job.requestUrl())
        if path == self._path:
            self._reply(job, b"text/html;charset=utf-8", self._html)
            return
        mime, _ = mimetypes.guess_type(path.name)
        if not mime or not mime.startswith("image/"):
            job.fail(QWebEngineUrlRequestJob.Error.RequestDenied)
            return
        try:
            data = path.read_bytes()
        except OSError:
            job.fail(QWebEngineUrlRequestJob.Error.UrlNotFound)
            return
        self._reply(job, mime.encode(), data)

    @staticmethod
    def _reply(job: QWebEngineUrlRequestJob, mime: bytes, data: bytes) -> None:
        buffer = QBuffer(job)
        buffer.setData(QByteArray(data))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        job.reply(mime, buffer)


class OfflineInterceptor(QWebEngineUrlRequestInterceptor):
    """Blocca qualsiasi accesso alla rete o a schemi non previsti."""

    def interceptRequest(self, info: QWebEngineUrlRequestInfo) -> None:
        if info.requestUrl().scheme() not in _ALLOWED_SCHEMES:
            info.block(True)


def create_profile(
    parent,
) -> tuple[QWebEngineProfile, DocumentSchemeHandler, OfflineInterceptor]:
    """Crea il profilo sicuro. Il chiamante deve conservare gestore e intercettore:
    PySide6 non lo fa e, se l'oggetto Python viene distrutto, Qt smette di chiamarlo."""
    # Un profilo senza nome è "off-the-record": nessuna cache o cookie su disco.
    profile = QWebEngineProfile(parent)
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
    profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
    )
    interceptor = OfflineInterceptor(profile)
    profile.setUrlRequestInterceptor(interceptor)
    handler = DocumentSchemeHandler(profile)
    profile.installUrlSchemeHandler(SCHEME, handler)

    attr = QWebEngineSettings.WebAttribute
    settings = profile.settings()
    for attribute, enabled in (
        (attr.JavascriptEnabled, False),
        (attr.JavascriptCanOpenWindows, False),
        (attr.JavascriptCanAccessClipboard, False),
        (attr.LocalStorageEnabled, False),
        (attr.LocalContentCanAccessRemoteUrls, False),
        (attr.LocalContentCanAccessFileUrls, False),
        (attr.PluginsEnabled, False),
        (attr.PdfViewerEnabled, False),
        (attr.WebGLEnabled, False),
        (attr.Accelerated2dCanvasEnabled, False),
        (attr.AutoLoadIconsForPage, False),
        (attr.NavigateOnDropEnabled, False),
        (attr.AutoLoadImages, True),
    ):
        settings.setAttribute(attribute, enabled)
    return profile, handler, interceptor


class ReaderPage(QWebEnginePage):
    """Pagina che decide dove portano i link cliccati nel documento."""

    open_document = Signal(Path)

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)
        self._current: Path | None = None

    def show_document(self, path: Path) -> None:
        self._current = path
        self.load(to_view_url(path))

    def acceptNavigationRequest(self, url: QUrl, nav_type, is_main_frame: bool) -> bool:
        scheme = url.scheme()
        if nav_type != QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            # Caricamenti avviati dall'applicazione (pagina iniziale con setHtml,
            # documento corrente), ancore e ricariche.
            if scheme == "data":
                return self._current is None
            return scheme == SCHEME.decode() and to_local_path(url) == self._current
        if scheme in _EXTERNAL_SCHEMES:
            QDesktopServices.openUrl(url)
            return False
        if scheme in (SCHEME.decode(), "file"):
            target = to_local_path(url)
            if target == self._current:
                return True  # ancora interna (note, indice)
            if is_markdown(target):
                self.open_document.emit(target)
        return False

    def createWindow(self, _type):
        return None

    def javaScriptConsoleMessage(self, *args) -> None:
        pass
