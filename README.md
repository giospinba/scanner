# ScannerPy

ScannerPy è uno strumento per verificare rapidamente lo stato del sistema e individuare problemi comuni.

## Cosa fa

- Controlla versione Python
- Verifica permessi di lettura/scrittura filesystem
- Controlla saturazione disco
- Esegue un check DNS di base
- Verifica presenza di tool minimi (`git`, `python3`)

## Avvio da terminale

```bash
python3 scannerpy.py
```

Output JSON:

```bash
python3 scannerpy.py --json
```

## Interfaccia grafica (senza terminale)

```bash
python3 scannerpy.py --gui
```

L'interfaccia mostra i controlli con stato:

- `OK` (verde)
- `WARNING` (arancione)
- `CRITICAL` (rosso)

## Test

```bash
python3 -m pytest -q
```
