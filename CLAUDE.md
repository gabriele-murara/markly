# markly

## Regole

- **NON FARE MAI COMMIT.** Non eseguire mai `git commit` (né `git commit --amend`,
  merge, rebase o altre operazioni che creano commit), nemmeno se sembra utile o
  implicito nel compito. I commit li fa esclusivamente l'utente.

## Nome del progetto

Il nome del progetto e dell'applicazione è **markly** (minuscolo). Usarlo sempre per
riferirsi al progetto: nel codice, nella documentazione, nei messaggi, nel packaging e
nelle conversazioni. Il vecchio nome provvisorio "MD Viewer" / `md_viewer` / `md-viewer`
non va più usato. Fanno eccezione `PROJECT_md_viewer.md` (la specifica originale, lasciata
invariata) e il nome della cartella di lavoro.

Identificatori derivati dal nome:
- pacchetto Python: `markly/` (`import markly`)
- comando e nome della distribuzione: `markly`
- file desktop: `packaging/markly.desktop`; spec PyInstaller: `packaging/markly.spec`
- schema URL interno di Qt WebEngine: `markly:`

## Il progetto

Lettore Markdown standalone per Linux, solo lettura: niente funzioni da editor o
accessorie (vedi le esclusioni in `PROJECT_md_viewer.md`). Priorità: compatibilità con i
documenti esistenti (CommonMark, estensioni diffuse, varianti vecchie) e sicurezza
dell'HTML incorporato.

Stack: Python ≥ 3.10, PySide6 (Qt for Python, LGPL) + Qt WebEngine, markdown-it-py +
mdit-py-plugins, nh3, Pygments. Non usare PyQt6: è GPL e impedirebbe di distribuire i
binari con la licenza MIT del progetto.
La versione dell'applicazione è nel file `.version` (letto da `markly.app.read_version`).

## Comandi

```bash
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest                              # test
.venv/bin/markly samples/extensions.md                  # avvio
.venv/bin/pyinstaller --noconfirm packaging/markly.spec # bundle in dist/markly/
```

Senza display (es. in sessioni remote) la GUI si prova con `QT_QPA_PLATFORM=offscreen`.
