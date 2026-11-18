# Studio di funzione

Inserisci f(x) e ottieni lo studio completo (dominio, simmetrie, segno, limiti, asintoti, derivate, estremi, flessi) con il grafico. Motore: SymPy in Pyodide. Grafico: Plotly.

## Web app
1. Carica il repository su GitHub (ramo `main`).
2. Settings → Pages → Source: **GitHub Actions**.
3. A ogni push il sito si aggiorna da solo.

## App Android
Actions → **Crea l'APK** → Run workflow. A fine build scarichi `studio-funzione-apk` da "Artifacts".
(In locale: `npm install`, `npx cap add android`, `npx cap sync`, `npx cap open android`.)

## Note
- Serve internet: Pyodide, Plotly e KaTeX arrivano da CDN. Per l'uso offline vanno copiati in `www/`.
- Sintassi: `x^2`, `sqrt(x)`, `exp(x)`, `ln(x)`, `sin(x)`, `abs(x)`, `2x` (prodotto implicito).
