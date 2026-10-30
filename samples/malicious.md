# Contenuti potenzialmente pericolosi

Nessuno degli elementi seguenti deve eseguire codice o accedere alla rete.

<script>document.body.innerHTML = "SCRIPT ESEGUITO";</script>

<img src="x" onerror="document.body.innerHTML='ONERROR ESEGUITO'">

<img src="https://example.com/tracker.png" alt="immagine remota (bloccata)">

<iframe src="https://example.com"></iframe>

<object data="file:///etc/passwd"></object>

<meta http-equiv="refresh" content="0; url=https://example.com">

<form action="https://example.com/steal"><input name="x" value="dati"><button>Invia</button></form>

<a href="javascript:alert(1)">link javascript</a> ·
[link javascript md](javascript:alert(1)) ·
<a href="data:text/html,<script>alert(1)</script>">link data</a>

<style>body { display: none }</style>

<svg onload="alert(1)"><circle r="10"/></svg>

<p style="background-image: url(https://example.com/bg.png)">Stile con url remoto</p>

Se leggi questo testo, il documento è stato reso in modo sicuro.
