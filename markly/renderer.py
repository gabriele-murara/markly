"""Conversione Markdown -> pagina HTML sicura.

Modulo indipendente dalla GUI: legge il file, lo converte con markdown-it-py
(CommonMark + estensioni diffuse) e sanitizza l'HTML risultante con nh3.
"""

from __future__ import annotations

import html
import re
from importlib import resources
from pathlib import Path

import nh3
from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

# Estensioni riconosciute come Markdown (filtro del dialogo e link interni).
MARKDOWN_EXTENSIONS = (
    ".md", ".markdown", ".mdown", ".mkd", ".mkdn", ".mdwn",
    ".mdtxt", ".mdtext", ".text", ".txt",
)

MAX_FILE_SIZE = 50 * 1024 * 1024


class DocumentError(Exception):
    """Errore di apertura o lettura di un documento, con messaggio per l'utente."""


# --- Lettura -----------------------------------------------------------------

def read_text(path: Path) -> str:
    """Legge un file di testo, gestendo le codifiche dei documenti più vecchi."""
    try:
        if path.is_dir():
            raise DocumentError(f"«{path}» è una cartella, non un file.")
        size = path.stat().st_size
        if size > MAX_FILE_SIZE:
            raise DocumentError(
                f"Il file è troppo grande ({size // (1024 * 1024)} MB, "
                f"massimo {MAX_FILE_SIZE // (1024 * 1024)} MB)."
            )
        data = path.read_bytes()
    except FileNotFoundError:
        raise DocumentError(f"File non trovato: «{path}».") from None
    except PermissionError:
        raise DocumentError(f"Permessi insufficienti per leggere «{path}».") from None
    except OSError as exc:
        raise DocumentError(f"Impossibile leggere «{path}»: {exc.strerror or exc}.") from None

    if b"\x00" in data[:8192] and not data.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise DocumentError(f"«{path.name}» non sembra un file di testo.")
    return decode(data)


def decode(data: bytes) -> str:
    """UTF-8 (con o senza BOM), UTF-16 con BOM, altrimenti Windows-1252/Latin-1."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp1252")
    except UnicodeDecodeError:
        return data.decode("latin-1")


# --- Normalizzazione delle varianti Markdown meno recenti ----------------------

_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
# Titolo ATX senza spazio dopo i cancelletti ("#Titolo"), accettato da Markdown.pl.
_ATX_NO_SPACE_RE = re.compile(r"^(#{1,6})([^\s#])")
_ATX_CLOSING_RE = re.compile(r"([^\s#])(#+)[ \t]*$")


def normalize(text: str) -> str:
    """Uniforma fine riga e adatta le sintassi tradizionali non CommonMark."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    fence: str | None = None
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if fence is not None:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
        elif m:
            fence = m.group(1)
        elif _ATX_NO_SPACE_RE.match(line):
            line = _ATX_NO_SPACE_RE.sub(r"\1 \2", line)
            lines[i] = _ATX_CLOSING_RE.sub(r"\1 \2", line)
    return "\n".join(lines)


# --- Parser ------------------------------------------------------------------

_formatter = HtmlFormatter(nowrap=True)


def _highlight(code: str, lang: str, _attrs: str) -> str:
    if not lang:
        return ""
    try:
        lexer = get_lexer_by_name(lang)
    except ClassNotFound:
        return ""
    return highlight(code, lexer, _formatter)


def _render_front_matter(self, tokens, idx, options, env) -> str:
    # Il front matter YAML resta visibile come blocco di codice, senza perdere contenuto.
    return f'<pre class="front-matter"><code>{html.escape(tokens[idx].content)}</code></pre>\n'


_WWW_LINK_RE = re.compile(r"""[^\s<>"]*[^\s<>".,;:!?)\]'*_~]""")


def _validate_www(self, text: str, pos: int) -> int:
    m = _WWW_LINK_RE.match(text, pos)
    return len(m.group(0)) if m and "." in m.group(0) else 0


def _normalize_www(self, match) -> None:
    match.url = "http://" + match.url


_SLUG_STRIP_RE = re.compile(r"[^\w\- ]")


def _heading_ids(state) -> None:
    """Aggiunge ai titoli id in stile GitHub, per i link interni (#sezione)."""
    seen: dict[str, int] = {}
    tokens = state.tokens
    for i, token in enumerate(tokens):
        if token.type != "heading_open" or token.attrGet("id"):
            continue
        text = "".join(
            child.content for child in tokens[i + 1].children or ()
            if child.type in ("text", "code_inline")
        )
        slug = _SLUG_STRIP_RE.sub("", text.strip().lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        token.attrSet("id", f"{slug}-{count}" if count else slug)


def _build_parser() -> MarkdownIt:
    md = (
        MarkdownIt("commonmark", {"html": True, "linkify": True, "highlight": _highlight})
        .enable(["table", "strikethrough", "linkify"])
        .use(front_matter_plugin)
        .use(footnote_plugin)
        .use(deflist_plugin)
        .use(tasklists_plugin)
    )
    md.add_render_rule("front_matter", _render_front_matter)
    md.core.ruler.push("heading_ids", _heading_ids)
    # Autolink solo per URL espliciti e "www." (come GFM): senza questa
    # restrizione nomi come "Markdown.pl" diventerebbero link a domini.
    md.linkify.set({"fuzzy_link": False})
    md.linkify.add("www.", {"validate": _validate_www, "normalize": _normalize_www})
    # Il controllo di sicurezza sugli URL è delegato a nh3: qui si accetta tutto,
    # così i link con schemi non comuni non vengono trasformati in testo.
    md.validateLink = lambda url: True
    return md


_parser = _build_parser()


# --- Sanitizzazione ----------------------------------------------------------

_TAGS = nh3.ALLOWED_TAGS | {"input", "tfoot", "font", "section", "label"}
_GENERIC_ATTRS = {"id", "class", "title", "lang", "dir", "align", "style"}
_ATTRIBUTES = {tag: set(attrs) for tag, attrs in nh3.ALLOWED_ATTRIBUTES.items()}
_ATTRIBUTES["*"] = _GENERIC_ATTRS
_ATTRIBUTES["a"] = {"href", "name"}
_ATTRIBUTES["font"] = {"color", "size", "face"}
_ATTRIBUTES["li"] = {"value"}
_ATTRIBUTES["ol"] = {"start", "type", "reversed"}
_ATTRIBUTES["td"] |= {"valign", "width"}
_ATTRIBUTES["th"] |= {"valign", "width"}
_ATTRIBUTES["table"] |= {"border", "cellpadding", "cellspacing", "width"}
_ATTRIBUTES["details"] = {"open"}
_TAG_VALUES = {"input": {"type": {"checkbox"}, "checked": {"checked", ""}, "disabled": {"disabled", ""}}}
_STYLE_PROPERTIES = {
    "color", "background-color", "text-align", "font-weight", "font-style",
    "font-size", "text-decoration", "vertical-align", "width", "height",
    "margin", "padding", "border", "float", "display",
}


_DATA_IMAGE_RE = re.compile(r"data:image/(png|gif|jpe?g|webp|bmp)[;,]", re.I)


def _attribute_filter(tag: str, attr: str, value: str) -> str | None:
    # Gli URL data: sono ammessi solo come immagini raster nei tag <img>.
    if value[:5].lower() == "data:" and attr in ("href", "src"):
        return value if tag == "img" and _DATA_IMAGE_RE.match(value) else None
    return value


def sanitize(fragment: str) -> str:
    return nh3.clean(
        fragment,
        tags=_TAGS,
        clean_content_tags={"script", "style", "noscript", "template"},
        attributes=_ATTRIBUTES,
        tag_attribute_values=_TAG_VALUES,
        set_tag_attribute_values={"input": {"disabled": "disabled"}},
        attribute_filter=_attribute_filter,
        url_schemes={"http", "https", "mailto", "file", "data", "ftp"},
        filter_style_properties=_STYLE_PROPERTIES,
        strip_comments=True,
        link_rel=None,
    )


# --- Pagina completa ---------------------------------------------------------

def _stylesheet() -> str:
    css = resources.files("markly").joinpath("style.css").read_text(encoding="utf-8")
    return css + "\n" + _formatter.get_style_defs(".highlight, pre code")


_CSS = _stylesheet()

_CSP = (
    "default-src 'none'; img-src markly: data:; style-src 'unsafe-inline'; "
    "form-action 'none'; frame-src 'none'; base-uri 'none'"
)


def render_body(text: str) -> str:
    """Markdown -> frammento HTML sanitizzato. Non perde mai il contenuto."""
    try:
        fragment = _parser.render(normalize(text))
    except Exception:  # noqa: BLE001 - qualsiasi errore del parser: mostra il sorgente
        return f"<pre class=\"raw\">{html.escape(text)}</pre>"
    return sanitize(fragment)


def render_page(text: str, title: str = "") -> str:
    return (
        "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
        f"<meta http-equiv=\"Content-Security-Policy\" content=\"{_CSP}\">"
        f"<title>{html.escape(title)}</title><style>{_CSS}</style></head>"
        f"<body><article class=\"markdown-body\">{render_body(text)}</article></body></html>"
    )
