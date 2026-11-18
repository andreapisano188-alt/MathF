const $ = id => document.getElementById(id);
const ESEMPI = ["(x^2-1)/(x-2)", "x*exp(-x)", "ln(x)/x", "x^3-3*x", "sin(x)/x", "sqrt(x^2-4)", "(x^2+1)/x"];
let py, analizza;

function stato(t, err) { $("stato").textContent = t; $("stato").className = err ? "err" : ""; }
function tex(el, s) { katex.render(s, el, { throwOnError: false }); }

async function avvia() {
  try {
    py = await loadPyodide();
    stato("Carico SymPy (solo la prima volta)…");
    await py.loadPackage(["numpy", "sympy"]);
    py.runPython(await (await fetch("analisi.py")).text());
    analizza = py.globals.get("analizza");
    $("vai").disabled = false;
    stato("Pronto.");
    studia();
  } catch (e) { stato("Errore nel caricamento: " + e.message, true); }
}

async function studia() {
  const testo = $("f").value.trim();
  if (!testo) return stato("Scrivi una funzione, ad esempio x^2-4.", true);
  stato("Calcolo in corso…");
  $("vai").disabled = true;
  await new Promise(r => setTimeout(r, 30));
  try {
    const d = JSON.parse(analizza(testo));
    if (d.errore) { stato(d.errore, true); return; }
    mostra(d);
    stato("");
  } catch (e) { stato("Errore: " + e.message, true); }
  finally { $("vai").disabled = false; }
}

function mostra(d) {
  $("out").hidden = false;
  const box = $("passi");
  box.innerHTML = "";
  d.steps.forEach(p => {
    const s = document.createElement("section");
    s.className = "passo";
    s.innerHTML = "<h2></h2>";
    s.firstChild.textContent = p.t;
    p.r.forEach(r => {
      const div = document.createElement("div");
      div.className = "r";
      if (r.s) div.append(r.s + " ");
      if (r.l) { const sp = document.createElement("span"); sp.className = "l"; tex(sp, r.l); div.append(sp); }
      s.append(div);
    });
    box.append(s);
  });
  grafico(d);
}

function grafico(d) {
  const st = getComputedStyle(document.body);
  const ink = st.getPropertyValue("--inchiostro").trim(), pen = st.getPropertyValue("--penna").trim(),
        ros = st.getPropertyValue("--rosso").trim(), gri = st.getPropertyValue("--griglia").trim();
  const traces = [{ x: d.x, y: d.y, mode: "lines", name: "f(x)", line: { color: pen, width: 3 }, connectgaps: false }];
  const shapes = [];
  const tratt = { color: ros, width: 1.5, dash: "dash" };
  d.av.forEach(a => shapes.push({ type: "line", x0: a, x1: a, yref: "paper", y0: 0, y1: 1, line: tratt }));
  d.ah.forEach(a => shapes.push({ type: "line", xref: "paper", x0: 0, x1: 1, y0: a, y1: a, line: tratt }));
  d.ao.forEach(([m, q]) => traces.push({ x: d.xr, y: d.xr.map(v => m * v + q), mode: "lines", name: "asintoto", line: tratt, hoverinfo: "skip", showlegend: false }));
  const stile = { "zero": ["circle", pen], "asse y": ["circle", pen], "massimo": ["triangle-up", ros], "minimo": ["triangle-down", ros], "flesso": ["diamond", "#b58900"] };
  const f2 = v => Number(v.toFixed(2));
  Object.keys(stile).forEach(t => {
    const q = d.pts.filter(p => p.t === t);
    if (!q.length) return;
    traces.push({ x: q.map(p => p.x), y: q.map(p => p.y), mode: "markers+text", name: t, marker: { symbol: stile[t][0], size: 11, color: stile[t][1], line: { color: ink, width: 1.5 } },
      text: q.map(p => `(${f2(p.x)}; ${f2(p.y)})`), textposition: "top center", textfont: { size: 11, color: ink } });
  });
  Plotly.newPlot("grafico", traces, {
    shapes, margin: { l: 44, r: 16, t: 16, b: 40 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: ink }, legend: { orientation: "h", y: -0.15 },
    xaxis: { range: d.xr, zeroline: true, zerolinecolor: ink, gridcolor: gri }, yaxis: { range: d.yr, zeroline: true, zerolinecolor: ink, gridcolor: gri }
  }, { responsive: true, displaylogo: false });
}

ESEMPI.forEach(e => {
  const b = document.createElement("button");
  b.textContent = e;
  b.onclick = () => { $("f").value = e; studia(); };
  $("es").append(b);
});
$("vai").onclick = studia;
$("f").addEventListener("keydown", e => { if (e.key === "Enter") studia(); });
$("png").onclick = () => Plotly.downloadImage("grafico", { format: "png", filename: "grafico", width: 1600, height: 1000, scale: 2 });
avvia();
