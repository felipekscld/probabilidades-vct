"""
Simula todos os caminhos válidos (double-elim, 8 equipes)
Gera: caminhos_campeonato_ok.json
"""

from __future__ import annotations
import itertools, json
from dataclasses import dataclass, field, replace
from typing import Dict, List, Tuple
import pandas as pd

# ── 1. Probabilidades (ELO) ───────────────────────────────────
elos = dict(zip(*pd.read_csv("elo_final_campeonato.csv").values.T))

def prob(a: str, b: str) -> float:
    return 1 / (1 + 10 ** ((elos[b] - elos[a]) / 400))

# ── 2. Equipes fixas e variáveis ──────────────────────────────
fixos      = ["G2", "XLG", "FNC", "RRQ"]
variaveis  = ["PRX", "SEN", "MIBR", "TH"]
permut     = list(itertools.permutations(variaveis))

# ── 3. Agenda oficial (place-holders T1-T4) ───────────────────
AGENDA: List[Tuple[str, str, str]] = [
    ("U1", "G2" , "T1"),
    ("U2", "XLG", "T2"),
    ("U3", "FNC", "T3"),
    ("U4", "RRQ", "T4"),
    ("U5", "W(U1)", "W(U2)"),
    ("U6", "W(U3)", "W(U4)"),
    ("L1", "L(U1)", "L(U2)"),
    ("L2", "L(U3)", "L(U4)"),
    ("L3", "W(L1)", "L(U5)"),
    ("L4", "W(L2)", "L(U6)"),
    ("L5", "W(L3)", "W(L4)"),
    ("U7", "W(U5)", "W(U6)"),
    ("L6", "W(L5)", "L(U7)"),
    ("GF", "W(U7)", "W(L6)"),
]

# ── 4. Estado do torneio ──────────────────────────────────────
@dataclass
class Estado:
    W: Dict[str, str] = field(default_factory=dict)      # vencedor por id
    L: Dict[str, str] = field(default_factory=dict)      # perdedor  por id
    derrotas: Dict[str, int] = field(default_factory=dict)
    hist: List[str] = field(default_factory=list)
    p: float = 1.0
    fim: bool = False
    campeao: str | None = None

    def clone(self) -> "Estado":
        return replace(self,
                       W=self.W.copy(),
                       L=self.L.copy(),
                       derrotas=self.derrotas.copy(),
                       hist=self.hist[:])

# ── 5. Resolve fontes A/B de cada partida ─────────────────────
def resolve(src: str, st: Estado) -> str:
    if src in elos:                 # time fixo
        return src
    tag, mid = src[0], src[2:-1]    # W(U1) → tag=W, mid=U1
    return (st.W if tag == "W" else st.L)[mid]

# ── 6. Próxima partida pendente ───────────────────────────────
def proxima(st: Estado, agenda):
    for mid, A, B in agenda:
        if mid not in st.W:
            try:
                a, b = resolve(A, st), resolve(B, st)
            except KeyError:
                return None
            if st.derrotas.get(a,0) < 2 and st.derrotas.get(b,0) < 2:
                return mid, a, b
    return None

# ── 7. Expande um estado ──────────────────────────────────────
def expandir(st: Estado, agenda) -> List[Estado]:
    nxt = proxima(st, agenda)
    if not nxt:
        return []
    mid, a, b = nxt
    pa, pb = prob(a,b), 1 - prob(a,b)
    filhos = []
    for vencedor, perdedor, pv in ((a,b,pa), (b,a,pb)):
        novo = st.clone()
        novo.hist.append(f"{mid}: {vencedor} > {perdedor} ({pv:.2%})")
        novo.p *= pv
        novo.W[mid] = vencedor
        novo.L[mid] = perdedor
        novo.derrotas[perdedor] = novo.derrotas.get(perdedor,0) + 1
        if mid == "GF":
            novo.fim, novo.campeao = True, vencedor
        filhos.append(novo)
    return [f for f in filhos
            if max(f.derrotas.values(), default=0) <= 2]

# ── 8. Simulação completa ─────────────────────────────────────
resultados = []
for perm in permut:
    subs = dict(zip(["T1","T2","T3","T4"], perm))
    agenda = [(mid,
               subs.get(A, A),
               subs.get(B, B)) for mid,A,B in AGENDA]

    inicial = Estado(derrotas={t:0 for t in fixos+list(perm)})
    pilha = [inicial]

    while pilha:
        est = pilha.pop()
        if est.fim:
            resultados.append({"caminho": est.hist,
                               "probabilidade": est.p,
                               "campeao": est.campeao})
        else:
            pilha.extend(expandir(est, agenda))

# ── 9. Salva JSON ─────────────────────────────────────────────
with open("caminhos_campeonato_ok.json","w",encoding="utf-8") as fp:
    json.dump(resultados, fp, ensure_ascii=False, indent=2)

print("Total de caminhos válidos:", len(resultados))
