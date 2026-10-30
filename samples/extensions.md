# Estensioni diffuse (GFM e simili)

## Tabelle

| Sinistra | Centro | Destra |
|:---------|:------:|-------:|
| a        |   b    |      c |
| `code`   | **bold** | ~~barrato~~ |

Tabella senza pipe esterni:

Nome | Valore
--- | ---
x | 1
y | 2

## Barrato

~~testo barrato~~

## Liste di attività

- [x] completato
- [ ] da fare
  - [x] sotto-attività

## Note a piè di pagina

Una frase con nota[^1] e un'altra[^lunga].

[^1]: Prima nota.
[^lunga]: Nota con **formattazione**.

## Liste di definizioni

Termine
: Definizione del termine.

## Autolink

Visita www.example.com oppure https://example.org/percorso?x=1.

## Codice con linguaggio

```js
const x = [1, 2, 3].map(n => n * 2);
```

```bash
echo "ciao" | tr a-z A-Z
```

## Link a un altro documento

[Apri unicode.md](unicode.md) — [vai alle note](#note-a-piè-di-pagina)
