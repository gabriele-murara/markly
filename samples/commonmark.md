# CommonMark standard

Paragrafo con *enfasi*, **grassetto**, ***entrambi*** e `codice inline`.
Riga con interruzione forzata  
(due spazi finali) e un\
backslash.

## Elenchi

1. Primo
2. Secondo
   - annidato A
   - annidato B
     1. profondo
3. Terzo

* stella
+ più
- meno

## Citazioni

> Citazione di primo livello
>
> > Citazione annidata con **grassetto**

## Codice

    blocco indentato
    di quattro spazi

```python
def saluta(nome: str) -> str:
    return f"Ciao {nome}"
```

~~~
blocco con tilde
~~~

## Link e immagini

[Link inline](https://commonmark.org "titolo"), [link di riferimento][cm], <https://spec.commonmark.org>.

[cm]: https://commonmark.org/help/

![Immagine locale](img/esempio.png)

---

Titolo setext
=============

Sottotitolo setext
------------------

Carattere escape: \*non corsivo\*, entità: &copy; &amp; &#8364;
