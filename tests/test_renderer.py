from pathlib import Path

import pytest

from markly.renderer import DocumentError, decode, read_text, render_body, render_page

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


# --- CommonMark --------------------------------------------------------------

def test_commonmark_basics():
    html = render_body("# T\n\n*e* **b** `c`\n\n> q\n\n---\n\n    code\n")
    for fragment in ("<h1", "<em>e</em>", "<strong>b</strong>", "<code>c</code>",
                     "<blockquote>", "<hr>", "<pre><code>code"):
        assert fragment in html


def test_nested_lists():
    html = render_body("1. a\n   - b\n     1. c\n2. d\n")
    assert html.count("<ol>") == 2 and "<ul>" in html


def test_setext_and_reference_links():
    html = render_body("Titolo\n======\n\n[x][1]\n\n[1]: http://example.com/ (T)\n")
    assert "<h1" in html and 'href="http://example.com/"' in html


def test_fenced_code_highlight():
    html = render_body("```python\ndef f(): pass\n```\n")
    assert '<span class="k">def</span>' in html


# --- Estensioni --------------------------------------------------------------

def test_table_and_strikethrough():
    html = render_body("a | b\n--- | ---\n1 | ~~2~~\n")
    assert "<table>" in html and "<s>2</s>" in html


def test_tasklist_footnote_deflist():
    html = render_body("- [x] fatto\n- [ ] no\n\nNota[^1]\n\n[^1]: testo\n\nT\n: def\n")
    assert 'type="checkbox"' in html and 'checked' in html and 'disabled' in html
    assert 'id="fn1"' in html and 'href="#fn1"' in html
    assert "<dl>" in html


def test_heading_anchors():
    assert 'id="note-a-piè-di-pagina"' in render_body("## Note a piè di pagina")


def test_autolinks():
    html = render_body("https://example.org e www.example.com. Markdown.pl")
    assert 'href="https://example.org"' in html
    assert 'href="http://www.example.com"' in html
    assert "Markdown.pl</a>" not in html


def test_front_matter_kept_visible():
    assert "title: x" in render_body("---\ntitle: x\n---\n# A\n")


# --- Varianti meno recenti ---------------------------------------------------

def test_atx_without_space():
    html = render_body("#Titolo#\n\n##Sotto\n\n## C#\n")
    assert '<h1 id="titolo">Titolo</h1>' in html
    assert ">Sotto</h2>" in html and ">C#</h2>" in html


def test_atx_fix_not_applied_in_code():
    html = render_body("```\n#include <stdio.h>\n```\n\n    #define X\n")
    assert "<h1" not in html and "#include" in html and "#define" in html


def test_legacy_html_preserved():
    html = render_body('<center>c</center>\n\n<font color="red">r</font>\n\n'
                       '<table border="1"><tr><td align="right">x</td></tr></table>\n')
    assert "<center>c</center>" in html and '<font color="red">' in html
    assert 'align="right"' in html


def test_unknown_syntax_is_not_lost():
    html = render_body("{: .classe } [[WikiLink]] <custom-tag>dentro</custom-tag>")
    assert "{: .classe }" in html and "[[WikiLink]]" in html and "dentro" in html


def test_crlf_and_cr_line_endings():
    assert render_body("# A\r\n\r\ntesto\rriga") == render_body("# A\n\ntesto\nriga")


# --- Sicurezza ---------------------------------------------------------------

@pytest.mark.parametrize("source, forbidden", [
    ("<script>alert(1)</script>", "alert"),
    ("<img src=x onerror=alert(1)>", "onerror"),
    ("[a](javascript:alert(1))", "javascript:"),
    ('<a href="vbscript:x">v</a>', "vbscript"),
    ('<a href="data:text/html,<script>x</script>">d</a>', "data:text"),
    ('<iframe src="https://evil"></iframe>', "iframe"),
    ('<object data="x"></object>', "object"),
    ('<meta http-equiv="refresh" content="0;url=https://evil">', "refresh"),
    ('<form action="https://evil"><button>b</button></form>', "form"),
    ("<style>body{display:none}</style>", "display"),
    ('<svg onload="alert(1)"></svg>', "onload"),
    ('<p style="background:url(https://evil/x.png)">p</p>', "url("),
    ('<base href="https://evil/">', "<base"),
])
def test_dangerous_content_removed(source, forbidden):
    assert forbidden not in render_body(source)


def test_data_image_allowed():
    assert 'src="data:image/png;base64,AAA"' in render_body("![i](data:image/png;base64,AAA)")


def test_page_has_csp():
    page = render_page("# x", "t")
    assert "Content-Security-Policy" in page and "default-src 'none'" in page


# --- Lettura file ------------------------------------------------------------

def test_decode_variants():
    assert decode("caffè".encode("utf-8")) == "caffè"
    assert decode(b"\xef\xbb\xbf# bom") == "# bom"
    assert decode("caffè €".encode("cp1252")) == "caffè €"
    assert decode("ciao".encode("utf-16")) == "ciao"


def test_read_samples():
    for path in SAMPLES.glob("*.md"):
        if path.name == "binary.md":
            continue
        assert render_body(read_text(path))


def test_read_errors(tmp_path):
    with pytest.raises(DocumentError, match="non trovato"):
        read_text(tmp_path / "manca.md")
    with pytest.raises(DocumentError, match="cartella"):
        read_text(tmp_path)
    with pytest.raises(DocumentError, match="testo"):
        read_text(SAMPLES / "binary.md")
    locked = tmp_path / "locked.md"
    locked.write_text("x")
    locked.chmod(0)
    try:
        with pytest.raises(DocumentError, match="Permessi"):
            read_text(locked)
    finally:
        locked.chmod(0o644)


def test_large_document():
    text = "## Sezione\n\nParagrafo con *testo* e `codice`.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n" * 5000
    html = render_body(text)
    assert html.count("<table>") == 5000
