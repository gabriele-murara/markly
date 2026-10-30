Ecco la issue riscritta per Claude Code, con supporto sia a CommonMark sia alle estensioni Markdown comunemente utilizzate nei file più vecchi, mantenendo l'applicazione essenziale e senza funzionalità superflue.

Issue — Lettore Markdown standalone per Linux

# Implementare un lettore Markdown standalone per Linux

## Obiettivo

Realizzare un'applicazione desktop standalone per Linux che consenta di aprire e leggere file Markdown, visualizzandone correttamente il contenuto formattato.

L'applicazione deve supportare sia **CommonMark sia il Markdown generico**, comprese le estensioni più diffuse e le varianti utilizzate nei documenti meno recenti.

L'obiettivo è offrire un lettore semplice, leggero e affidabile, senza funzionalità da editor.

## Funzionalità richieste

### 1\. Apertura dei file

- Permettere di aprire un file tramite una finestra di selezione del filesystem.
- Permettere di aprire un file passando il percorso come argomento da riga di comando.
- Supportare le estensioni `.md`, `.markdown`, `.mdown`, `.mkd` e altre estensioni Markdown comuni.
- Gestire correttamente gli errori di apertura e lettura.

### 2\. Rendering Markdown

Visualizzare il documento formattato, anziché mostrare il sorgente Markdown.

Il parser deve supportare:

- CommonMark.
- Markdown tradizionale e le estensioni più diffuse.
- Titoli, paragrafi, enfasi, grassetto ed elenchi ordinati e non ordinati.
- Citazioni e blocchi di codice.
- Codice inline.
- Link e immagini.
- Tabelle.
- Separazioni orizzontali.
- Liste annidate.
- Liste di attività con caselle di controllo, quando supportate dall'estensione Markdown utilizzata.
- Note a piè di pagina, barrato e altri costrutti diffusi, quando supportati dal parser scelto.
- Blocchi HTML incorporati nei documenti Markdown, nei limiti previsti dal motore di rendering.

Il rendering deve essere robusto anche con documenti vecchi, formattazioni non uniformi e sintassi tipiche delle diverse implementazioni Markdown.

Non è necessario implementare manualmente le singole regole: utilizzare una libreria Markdown consolidata, configurandola per supportare CommonMark e le estensioni più comuni.

Quando una sintassi non è riconosciuta, il lettore deve evitare di perdere il contenuto originale, per quanto tecnicamente possibile.

### 3\. Lettura e navigazione

- Visualizzare il contenuto in un'area dedicata alla lettura.
- Supportare lo scorrimento verticale.
- Garantire una visualizzazione leggibile anche per documenti lunghi.
- Gestire correttamente i caratteri UTF-8 e il testo multilingue.
- Consentire la selezione del testo renderizzato e la copia negli appunti tramite le normali funzionalità del sistema operativo.
- Mantenere i link visivamente distinguibili e, quando appropriato, cliccabili.

### 4\. Interfaccia grafica

L'interfaccia deve essere minimale e comprendere esclusivamente:

- Una finestra principale.
- Un comando per aprire un file.
- Un'area di visualizzazione del documento.
- Il titolo della finestra aggiornato in base al file aperto.

Non sono necessarie altre funzionalità.

## Requisiti tecnici

- Applicazione desktop destinata a Linux.
- Architettura semplice, con codice facilmente manutenibile.
- Utilizzo di librerie esistenti e consolidate per il parsing e il rendering Markdown.
- Supporto ai formati Markdown più comuni senza vincolare l'applicazione a una singola variante.
- Gestione sicura dei contenuti HTML incorporati: non eseguire script e impedire comportamenti pericolosi derivanti dal contenuto dei documenti.
- Nessuna dipendenza da servizi online per aprire e visualizzare i file.
- Preferenza per una distribuzione standalone, con dipendenze ridotte al minimo.

Scegli autonomamente lo stack tecnologico più adatto, privilegiando semplicità, stabilità e facilità di distribuzione.

## Esclusioni

Non implementare:

- Modifica dei documenti.
- Salvataggio o esportazione.
- Editor Markdown.
- Visualizzazione affiancata del sorgente.
- Schede multiple.
- Gestione di progetti o raccolte di documenti.
- Plugin.
- Account o sincronizzazione.
- Funzionalità AI.
- Personalizzazioni estetiche avanzate.
- Funzionalità aggiuntive non esplicitamente richieste.

## Verifica

Verificare il funzionamento dell'applicazione con documenti di esempio che includano:

- Markdown CommonMark standard.
- Tabelle e altri costrutti tipici delle estensioni Markdown.
- Documenti scritti secondo varianti Markdown meno recenti.
- Blocchi HTML incorporati.
- Testo Unicode e multilingue.
- Link, immagini, elenchi annidati e blocchi di codice.

Verificare inoltre che:

- I file possano essere aperti sia dall'interfaccia sia da riga di comando.
- Il testo visualizzato possa essere selezionato e copiato.
- Gli errori di lettura siano gestiti correttamente.
- I contenuti dei documenti non possano eseguire codice arbitrario.
- L'applicazione possa essere compilata e avviata su Linux seguendo istruzioni documentate.

## Criterio di completamento

L'applicazione deve consentire di aprire un file Markdown, visualizzarlo correttamente anche se proviene da una variante Markdown diversa da CommonMark e copiarne il testo.

**La priorità è la compatibilità con i documenti esistenti, non la quantità di funzionalità.**

Non trasformare il progetto in un editor: deve rimanere esclusivamente un lettore Markdown standalone, semplice e affidabile.
