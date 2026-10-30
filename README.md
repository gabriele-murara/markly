# markly

**markly** è un lettore Markdown per Linux: apre un file Markdown e lo mostra
formattato, pronto da leggere.

Fa solo questo, di proposito. Non è un editor: non modifica, non salva, non esporta e non
ha schede, progetti, plugin o funzioni accessorie. La priorità è mostrare correttamente
qualsiasi documento Markdown esistente, compresi quelli scritti anni fa con varianti
diverse da CommonMark.

## Installazione (Lubuntu / Ubuntu 24.04)

```bash
sudo make deps        # pacchetti di sistema, una volta sola
make                  # ambiente virtuale, test e bundle in dist/markly/
sudo make install     # installa in /usr/local, con voce nel menu delle applicazioni
```

Per installare solo per il proprio utente, senza sudo: `make install PREFIX=$HOME/.local`.
Si disinstalla con `sudo make uninstall` (oppure con lo stesso `PREFIX` usato per installare).

## Uso

```bash
markly                  # apre la finestra vuota
markly documento.md     # apre direttamente il documento
markly --version        # mostra la versione ed esce
```

| Azione | Come |
|---|---|
| Aprire un documento | **File → Apri…** oppure **Ctrl+O** |
| Uscire | **File → Esci** oppure **Ctrl+Q** |
| Copiare il testo | selezione con il mouse, poi **Ctrl+C** o menu contestuale → Copia |
| Selezionare tutto | **Ctrl+A** o menu contestuale → Seleziona tutto |
| Cercare nel documento | **Ctrl+F**; **Invio** / **Maiusc+Invio** per la corrispondenza successiva / precedente; **Esc** o un clic nel documento per chiudere |

Il titolo della finestra mostra il nome del documento aperto (`documento.md — markly`).

Il dialogo di apertura mostra i file con estensione `.md`, `.markdown`, `.mdown`, `.mkd`,
`.mkdn`, `.mdwn`, `.mdtxt`, `.mdtext`, `.text` e `.txt`. Con il filtro **Tutti i file** si
può aprire qualsiasi file di testo.

### Link

| Link nel documento | Cosa succede |
|---|---|
| `http://`, `https://`, `ftp://`, `mailto:` | si apre con il browser o il client di posta del sistema |
| altro documento Markdown locale (`altro.md`) | si apre in markly, al posto di quello corrente |
| ancora interna (`#sezione`, note a piè di pagina) | la pagina scorre fino al punto indicato |
| qualsiasi altro link (file non Markdown, `javascript:`, …) | viene ignorato |

I titoli ricevono automaticamente un identificatore in stile GitHub, quindi funzionano
anche link come `[vai](#note-a-piè-di-pagina)`.

### Errori

Se un file non si può aprire, markly mostra un messaggio che spiega il motivo e lascia
visibile il documento già aperto. I casi gestiti sono: file inesistente, cartella al posto
di un file, permessi insufficienti, file non testuale (binario) e file più grande di 50 MB.

## Cosa sa visualizzare

Il Markdown viene interpretato da
[markdown-it-py](https://github.com/executablebooks/markdown-it-py), configurato in
modalità CommonMark con le estensioni più diffuse.

**CommonMark:** titoli (`#` e sottolineati con `===`/`---`), paragrafi, corsivo, grassetto,
elenchi ordinati e non ordinati anche annidati, citazioni, codice inline, blocchi di codice
indentati o tra ```` ``` ````/`~~~`, link e immagini (anche di riferimento), separatori
orizzontali, interruzioni di riga, entità HTML e HTML incorporato.

**Estensioni:**
- tabelle, con allineamento delle colonne;
- testo barrato (`~~testo~~`);
- liste di attività (`- [x] fatto`), mostrate con caselle di sola lettura;
- note a piè di pagina (`[^1]`);
- liste di definizioni (`Termine` / `: definizione`);
- link automatici per gli indirizzi che iniziano con `http://`, `https://` o `www.`;
- colorazione della sintassi nei blocchi di codice che indicano il linguaggio
  (```` ```python ````), tramite [Pygments](https://pygments.org);
- front matter YAML in testa al file, mostrato come blocco di codice.

**Documenti meno recenti:** markly accetta anche sintassi che CommonMark non prevede ma che
erano comuni nelle prime implementazioni di Markdown:
- titoli senza spazio dopo il cancelletto (`#Titolo` o `##Titolo##`, come in Markdown.pl);
- HTML in stile anni 2000: `<center>`, `<font color="…">`, attributi `align`, tabelle HTML
  con `border`, `cellpadding`, ecc.;
- fine riga Windows (`CRLF`) e Mac classico (`CR`);
- codifiche diverse da UTF-8 (vedi sotto).

**Nessun contenuto perso:** la sintassi che il parser non riconosce (per esempio `[[WikiLink]]`
o gli attributi `{: .classe }`) resta visibile come testo. Se il parser fallisse, markly
mostrerebbe il sorgente del documento invece di una pagina vuota.

### Codifica dei caratteri

markly riconosce automaticamente la codifica del file, in quest'ordine:

1. UTF-16, se il file inizia con il relativo BOM;
2. UTF-8, con o senza BOM;
3. Windows-1252, la codifica tipica dei documenti scritti su Windows in Europa occidentale;
4. Latin-1 (ISO-8859-1), che accetta qualsiasi sequenza di byte.

Il testo multilingue (alfabeti non latini, CJK, scritture da destra a sinistra, emoji) viene
mostrato correttamente, purché il sistema abbia i font necessari.

### Aspetto

Il documento è impaginato in una colonna di larghezza contenuta, leggibile anche per testi
lunghi. I colori seguono automaticamente il tema chiaro o scuro del sistema. Non ci sono
opzioni di personalizzazione grafica.

## Sicurezza

Un documento Markdown può contenere HTML arbitrario. markly lo considera non affidabile e
usa più protezioni indipendenti, in modo che un documento non possa eseguire codice né
comunicare con l'esterno:

1. **Sanitizzazione.** L'HTML prodotto passa da [nh3](https://github.com/messense/nh3), che
   lascia passare solo un elenco di tag e attributi di contenuto. Vengono eliminati, tra
   gli altri, `<script>`, `<style>`, `<iframe>`, `<object>`, `<form>`, `<meta>`, i gestori di
   eventi (`onclick`, `onerror`, …) e gli URL `javascript:`, `vbscript:` e `data:` (tranne le
   immagini raster). Il testo contenuto nei tag rimossi viene conservato, salvo per script e
   stili.
2. **JavaScript disattivato** nel motore di visualizzazione, insieme a plugin, WebGL, storage
   locale e apertura di nuove finestre.
3. **Content-Security-Policy** restrittiva in ogni pagina: sono ammesse solo le immagini
   locali e gli stili interni.
4. **Nessun accesso alla rete.** Un intercettore blocca ogni richiesta che non sia per il
   documento o per un'immagine locale. Le immagini remote non vengono caricate; il loro testo
   alternativo resta visibile.
5. **Navigazione controllata.** I clic sui link seguono le regole della tabella *Link*: la
   vista non lascia mai il documento per caricare pagine esterne.
6. **Nessuna traccia su disco.** Il motore di visualizzazione usa un profilo temporaneo,
   senza cache, cookie o dati salvati.

markly funziona completamente offline e non contatta alcun servizio.

## Come funziona

```
file su disco
   │  lettura, controlli e riconoscimento della codifica      renderer.read_text()
   ▼
testo
   │  normalizzazione: fine riga, titoli vecchio stile         renderer.normalize()
   ▼
   │  parsing Markdown → HTML (markdown-it-py + plugin)
   │  sanitizzazione dell'HTML (nh3)                          renderer.render_body()
   ▼
pagina HTML completa (stile, CSP)                              renderer.render_page()
   │
   ▼
schema interno markly:  →  Qt WebEngine (JS disattivato, rete bloccata)
```

1. **Lettura** (`markly/renderer.py`). Il file viene letto, controllato (esistenza, permessi,
   dimensione, contenuto binario) e decodificato.
2. **Normalizzazione.** I fine riga vengono uniformati e i titoli senza spazio vengono
   riscritti nella forma CommonMark, saltando i blocchi di codice.
3. **Conversione e sanitizzazione.** markdown-it-py produce l'HTML, che viene ripulito da nh3
   e inserito in una pagina completa con il foglio di stile (`markly/style.css`) e la
   Content-Security-Policy.
4. **Visualizzazione** (`markly/security.py`, `markly/app.py`). La pagina è servita a Qt
   WebEngine attraverso uno schema URL interno, `markly:`, che usa lo stesso percorso del file
   sul disco. In questo modo immagini relative, link ad altri documenti e ancore interne
   funzionano come se la pagina fosse accanto al file. Lo schema restituisce solo il documento
   corrente e i file immagine locali, mai altri file.

La finestra (`markly/app.py`) contiene soltanto il menu **File**, la vista del documento e
la barra di ricerca, nascosta finché non si preme Ctrl+F.
La versione è scritta solo nel file `.version` nella radice del progetto: la legge
`markly --version` e, in fase di installazione, anche `pyproject.toml`.

### Struttura del codice

```
markly/
  __main__.py     avvio con "python -m markly"
  app.py          finestra principale, apertura dei file, riga di comando, versione
  renderer.py     lettura dei file, Markdown → HTML sanitizzato, pagina completa
  security.py     configurazione sicura di Qt WebEngine, schema markly:, gestione dei link
  style.css       foglio di stile di lettura (tema chiaro e scuro)
packaging/        file .desktop e configurazione PyInstaller
samples/          documenti di prova
tests/            test automatici
.version          versione dell'applicazione
```

### Tecnologie

- [Python](https://www.python.org) ≥ 3.10
- [PySide6](https://doc.qt.io/qtforpython-6/) (Qt for Python) e Qt WebEngine: finestra e
  visualizzazione HTML
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py) e
  [mdit-py-plugins](https://github.com/executablebooks/mdit-py-plugins): parsing Markdown
- [linkify-it-py](https://github.com/tsutsu3/linkify-it-py): link automatici
- [nh3](https://github.com/messense/nh3): sanitizzazione HTML
- [Pygments](https://pygments.org): colorazione della sintassi

## Documenti di prova e test

La cartella `samples/` contiene documenti per verificare il comportamento:

| File | Contenuto |
|---|---|
| `commonmark.md` | costrutti CommonMark standard |
| `extensions.md` | tabelle, barrato, liste di attività, note, definizioni, autolink, codice |
| `legacy.md` | sintassi Markdown.pl e HTML vecchio stile |
| `html_embedded.md` | HTML incorporato (`<details>`, `<kbd>`, immagini, stili inline) |
| `unicode.md` | testo multilingue, scritture da destra a sinistra, emoji |
| `latin1.md` | file in codifica Latin-1/Windows-1252 |
| `malicious.md` | contenuti pericolosi che devono essere neutralizzati |
| `binary.md` | file non testuale, per verificare il messaggio d'errore |

I test automatici in `tests/` verificano conversione, compatibilità, sanitizzazione, lettura
dei file e gestione della versione. Si eseguono con `python -m pytest`.

## Limiti noti

- La conversione è scritta in Python: un documento normale si apre all'istante, ma un file di
  diversi megabyte può richiedere qualche secondo (circa 200 KB al secondo).
- Le immagini remote non vengono mai caricate, per scelta.
- I link a file locali che non sono Markdown (PDF, immagini, …) vengono ignorati, per non
  aprire con il sistema file potenzialmente pericolosi.
- Le liste annidate con un rientro inferiore a quello richiesto da CommonMark (per esempio due
  spazi sotto un elemento numerato) vengono mostrate come liste allo stesso livello; il
  contenuto resta comunque visibile.

## Licenza

markly è distribuito con licenza [MIT](LICENSE) © 2026 Gabriele Murara.

Chiunque può usarlo, copiarlo, modificarlo, unirlo ad altri progetti, pubblicarlo,
ridistribuirlo e venderlo, anche in forma modificata, a condizione di mantenere
l'avviso di copyright con il nome dell'autore e il testo della licenza.
