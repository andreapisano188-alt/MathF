import json
import numpy as np
from sympy import *
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
from sympy.calculus.util import continuous_domain, periodicity
from sympy.solvers.inequalities import solve_univariate_inequality

x = Symbol('x', real=True)
TR = standard_transformations + (implicit_multiplication_application, convert_xor)
LOC = {'x': x, 'e': E, 'ln': log, 'sen': sin, 'tg': tan, 'arctg': atan}


def num(e):
    try:
        v = complex(N(e))
        return v.real if abs(v.imag) < 1e-12 else None
    except Exception:
        return None


def approx(c):
    t = latex(c)
    if not c.is_Rational and num(c) is not None:
        t += r"\approx " + str(round(num(c), 4))
    return t


def radici_num(g, a=-30, b=30, n=6000):
    fn = lambdify(x, g, 'numpy')
    xs = np.linspace(a, b, n)
    with np.errstate(all='ignore'):
        ys = np.real(fn(xs) * np.ones_like(xs))
    out = []
    for i in range(n - 1):
        y0, y1 = ys[i], ys[i + 1]
        if np.isfinite(y0) and np.isfinite(y1) and y0 * y1 < 0 and abs(y0) < 1e3 and abs(y1) < 1e3:
            lo, hi = xs[i], xs[i + 1]
            for _ in range(60):
                m = (lo + hi) / 2
                if np.real(fn(lo)) * np.real(fn(m)) <= 0:
                    hi = m
                else:
                    lo = m
            out.append(Float((lo + hi) / 2))
    return out


def trova(g, D):
    try:
        s = solveset(g, x, D)
        if s.is_FiniteSet:
            return sorted(list(s), key=lambda p: num(p) or 0)
    except Exception:
        pass
    return [r for r in radici_num(g) if D.contains(r) == True]


def lim(expr, pt, d='+-'):
    try:
        return limit(expr, x, pt, d)
    except Exception:
        return None


def valido(v):
    return v is not None and v != nan and (v.is_extended_real is True or isinstance(v, AccumBounds))


def ltx(v):
    return r"\text{non esiste}" if isinstance(v, AccumBounds) else latex(v)


def insieme(g, D, verso):
    try:
        s = solve_univariate_inequality(g > 0 if verso > 0 else g < 0, x, relational=False, domain=D)
        return latex(s)
    except Exception:
        return None


def analizza(testo):
    try:
        return json.dumps(_analizza(testo))
    except Exception as ex:
        return json.dumps({"errore": "Non riesco a leggere o analizzare la funzione: " + str(ex)})


def _analizza(testo):
    steps, pts = [], []
    av, ah, ao = [], [], []

    def add(t, righe):
        steps.append({"t": t, "r": [r for r in righe if r]})

    f = parse_expr(testo, local_dict=LOC, transformations=TR)
    if f.free_symbols - {x}:
        raise ValueError("usa solo la variabile x")
    add("Funzione", [{"l": "f(x)=" + latex(f)}])

    # Dominio
    try:
        D = continuous_domain(f, x, S.Reals)
    except Exception:
        D = S.Reals
    add("Dominio", [{"l": r"\mathrm{dom}\,f=" + latex(D)}])
    try:
        bordo = sorted([p for p in D.boundary if p.is_number and p.is_finite], key=lambda p: num(p) or 0)
    except Exception:
        bordo = []

    # Simmetrie e periodicità
    try:
        if simplify(f.subs(x, -x) - f) == 0:
            par = "Funzione pari: f(−x) = f(x), grafico simmetrico rispetto all'asse y."
        elif simplify(f.subs(x, -x) + f) == 0:
            par = "Funzione dispari: f(−x) = −f(x), grafico simmetrico rispetto all'origine."
        else:
            par = "Né pari né dispari."
    except Exception:
        par = "Simmetria non determinata."
    try:
        per = periodicity(f, x)
    except Exception:
        per = None
    add("Simmetrie e periodicità", [{"s": par}, {"s": "Periodica, periodo", "l": latex(per)} if per is not None else {"s": "Non periodica."}])

    # Intersezioni e segno
    righe = []
    if D.contains(0) == True:
        y0 = simplify(f.subs(x, 0))
        righe.append({"s": "Con l'asse y:", "l": "f(0)=" + latex(y0)})
        if num(y0) is not None:
            pts.append({"x": 0.0, "y": num(y0), "t": "asse y"})
    zeri = trova(f, D)
    for z in zeri:
        righe.append({"s": "Zero:", "l": "x=" + approx(z)})
        pts.append({"x": num(z), "y": 0.0, "t": "zero"})
    if not zeri:
        righe.append({"s": "Nessun zero (intersezione con l'asse x)."})
    add("Intersezioni con gli assi", righe)
    pos, neg = insieme(f, D, 1), insieme(f, D, -1)
    add("Segno", [{"s": "f(x) > 0 per", "l": "x\\in " + pos} if pos else None,
                  {"s": "f(x) < 0 per", "l": "x\\in " + neg} if neg else None])

    # Limiti e asintoti
    righe = []
    for p in bordo:
        sx, dx = lim(f, p, '-'), lim(f, p, '+')
        for v, seg, nome in ((sx, '-', 'sinistra'), (dx, '+', 'destra')):
            if valido(v):
                righe.append({"s": "Limite da " + nome + ":", "l": r"\lim_{x\to %s^{%s}} f(x)=%s" % (latex(p), seg, ltx(v))})
        if any(valido(v) and v in (oo, -oo) for v in (sx, dx)):
            av.append(num(p))
    for lab, pt, dom_ok in (("+\\infty", oo, D.sup == oo), ("-\\infty", -oo, D.inf == -oo)):
        if not dom_ok:
            continue
        v = lim(f, pt)
        if not valido(v):
            continue
        righe.append({"l": r"\lim_{x\to %s} f(x)=%s" % (lab, ltx(v))})
        if isinstance(v, AccumBounds):
            continue
        if v.is_finite:
            ah.append(num(v))
            righe.append({"s": "Asintoto orizzontale", "l": "y=" + latex(v)})
        else:
            m = lim(f / x, pt)
            if m is not None and m.is_finite and m != 0:
                q = lim(f - m * x, pt)
                if q is not None and q.is_finite:
                    ao.append([num(m), num(q)])
                    righe.append({"s": "Asintoto obliquo", "l": "y=" + latex(simplify(m * x + q))})
    for a in sorted(set(av)):
        righe.append({"s": "Asintoto verticale", "l": "x=" + str(round(a, 4))})
    add("Limiti e asintoti", righe)

    # Derivata prima
    f1 = simplify(diff(f, x))
    crit = trova(f1, D)
    righe = [{"l": "f'(x)=" + latex(f1)}]
    for c in crit:
        y = simplify(f.subs(x, c))
        v2 = num(diff(f1, x).subs(x, c))
        tipo = None
        if v2 is not None and v2 > 1e-12:
            tipo = "minimo"
        elif v2 is not None and v2 < -1e-12:
            tipo = "massimo"
        else:
            a, b = num(f1.subs(x, c - 1e-3)), num(f1.subs(x, c + 1e-3))
            if a is not None and b is not None:
                tipo = "minimo" if a < 0 < b else "massimo" if a > 0 > b else "stazionario (non è un estremo)"
        righe.append({"s": "Punto stazionario (" + (tipo or "da verificare") + "):", "l": "x=%s,\\; f(x)=%s" % (approx(c), approx(y))})
        if tipo in ("minimo", "massimo") and num(y) is not None:
            pts.append({"x": num(c), "y": num(y), "t": tipo})
    cr, de = insieme(f1, D, 1), insieme(f1, D, -1)
    righe += [{"s": "Crescente per", "l": "x\\in " + cr} if cr else None,
              {"s": "Decrescente per", "l": "x\\in " + de} if de else None]
    add("Derivata prima: monotonia ed estremi", righe)

    # Derivata seconda
    f2 = simplify(diff(f1, x))
    righe = [{"l": "f''(x)=" + latex(f2)}]
    for c in trova(f2, D):
        a, b = num(f2.subs(x, c - 1e-3)), num(f2.subs(x, c + 1e-3))
        if a is not None and b is not None and a * b < 0:
            y = simplify(f.subs(x, c))
            righe.append({"s": "Flesso:", "l": "x=%s,\\; f(x)=%s" % (approx(c), approx(y))})
            if num(y) is not None:
                pts.append({"x": num(c), "y": num(y), "t": "flesso"})
    cv, cc = insieme(f2, D, 1), insieme(f2, D, -1)
    righe += [{"s": "Concava verso l'alto (convessa) per", "l": "x\\in " + cv} if cv else None,
              {"s": "Concava verso il basso per", "l": "x\\in " + cc} if cc else None]
    add("Derivata seconda: concavità e flessi", righe)

    # Campionamento per il grafico
    xs = [p["x"] for p in pts] + av
    lo = max(min(xs + [-5]) - 2, -60)
    hi = min(max(xs + [5]) + 2, 60)
    fn = lambdify(x, f, 'numpy')
    X = np.linspace(lo, hi, 2500)
    with np.errstate(all='ignore'):
        Y = fn(X) * np.ones_like(X)
        if np.iscomplexobj(Y):
            Y = np.where(np.abs(Y.imag) < 1e-9, Y.real, np.nan)
        Y = Y.astype(float)
        cap = max(10.0, 3 * max([abs(p["y"]) for p in pts] + [0]))
        Y[~np.isfinite(Y) | (np.abs(Y) > cap)] = np.nan
        salti = np.abs(np.diff(Y)) > cap
        Y[1:][salti] = np.nan
    fin = Y[np.isfinite(Y)]
    ys = list(fin) + [p["y"] for p in pts]
    yr = [min(ys), max(ys)] if ys else [-5, 5]
    pad = (yr[1] - yr[0]) * 0.1 or 1
    return {
        "steps": steps,
        "x": [round(float(v), 5) for v in X],
        "y": [None if not np.isfinite(v) else round(float(v), 6) for v in Y],
        "pts": pts, "av": sorted(set(av)), "ah": sorted(set(ah)), "ao": ao,
        "xr": [lo, hi], "yr": [yr[0] - pad, yr[1] + pad],
    }
