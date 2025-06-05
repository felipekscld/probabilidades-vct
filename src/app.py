import streamlit as st
import pandas as pd
import re, os, random, itertools, io
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Rectangle

# ───────────────────── Arquivos de dados ─────────────────────
PARQUET = "data/caminhos.parquet"
LOGOS   = "logos"
ELO_CSV = "data/elo_final_campeonato.csv"

# ─────────────────── Função load_data ────────────────────────
@st.cache_resource
def load_data():
    df = pd.read_parquet(PARQUET)
    df["probabilidade"] = df["probabilidade"].astype(float)
    norm = lambda s: re.sub(r"[^A-Za-z0-9]", "", s).upper()
    df["campeao_clean"] = df["campeao"].apply(norm)
    return df, sorted(df["campeao_clean"].unique())

# ─────────────────── Constantes visuais ──────────────────────
BOX_W, BOX_H = 2.6, 1.5
GAP_X, DY    = 0.28, 0.40
ZOOM         = 0.08

# ──────────────── Dados de elo (para probabilidades) ─────────
df_elo = pd.read_csv(ELO_CSV)
elos   = dict(zip(df_elo["time"], df_elo["elo_final"]))

# ─────────────────── Layout fixo do bracket ──────────────────
COL = {"qf": -0.2, "sf": 2.6, "uf": 5.4, "gf": 8.2}
POS = {  
    "U1": (COL["qf"], 10), "U2": (COL["qf"],  8),
    "U3": (COL["qf"],  6), "U4": (COL["qf"],  4),
    "U5": (COL["sf"],  9), "U6": (COL["sf"],  5),
    "U7": (COL["uf"],  7),
    "L1": (COL["qf"],  1.5), "L2": (COL["qf"], -0.5),
    "L3": (COL["sf"],  1.5), "L4": (COL["sf"], -0.5),
    "L5": (COL["uf"],  0.5), "L6": (COL["gf"],  1.5),
    "GF": (COL["gf"],  7),
}
LABEL_PAD = 0.25
PHASE_TO_TOP = {
    "Upper Quarterfinals": "U1",
    "Upper Semifinals":    "U5",
    "Upper Final":         "U7",
    "Grand Final":         "GF",
    "Lower Round 1":       "L1",
    "Lower Round 2":       "L3",
    "Lower Round 3":       "L5",
    "Lower Final":         "L6",
}
PHASE_LABELS = {
    lbl: (POS[mid][0], POS[mid][1] + BOX_H/2 + LABEL_PAD)
    for lbl, mid in PHASE_TO_TOP.items()
}

# ────────────── Nomes das partidas ──────────────────
PHASE_DISPLAY = {
    "U1": "Upper Quarterfinal 1",
    "U2": "Upper Quarterfinal 2",
    "U3": "Upper Quarterfinal 3",
    "U4": "Upper Quarterfinal 4",
    "U5": "Upper Semifinal 1",
    "U6": "Upper Semifinal 2",
    "L1": "Lower Round 1.1",
    "L2": "Lower Round 1.2",
    "L3": "Lower Round 2.1",
    "L4": "Lower Round 2.2",
    "L5": "Lower Round 3",
    "U7": "Upper Final",
    "L6": "Lower Final",
    "GF": "Grand Final",
}

# ───────────────────────── Helpers ───────────────────────────
def logo(team: str):
    f = os.path.join(LOGOS, f"{team}.png")
    return OffsetImage(plt.imread(f), zoom=ZOOM) if os.path.exists(f) else None

def draw_box(ax, x, y, win, lose, prob):
    ax.add_patch(Rectangle((x, y-BOX_H/2), BOX_W, BOX_H,
                           fc="white", ec="black"))
    if (img := logo(win)):
        ax.add_artist(AnnotationBbox(img, (x+0.15, y+DY), frameon=False))
    ax.text(x+0.15+GAP_X, y+DY, win, weight="bold", va="center", fontsize=8)
    ax.text(x+BOX_W-0.30, y+DY, f"{prob:.0f}%",
            ha="right", va="center", fontsize=8)
    ax.text(x+BOX_W-0.10, y+DY, "✔", color="green",
            ha="right", va="center")
    if (img2 := logo(lose)):
        ax.add_artist(AnnotationBbox(img2, (x+0.15, y-DY), frameon=False))
    ax.text(x+0.15+GAP_X, y-DY, lose, va="center", fontsize=8)

def parse_path(lines):
    d={}
    for ln in lines:
        fase, resto = ln.split(":",1)
        w, resto2   = resto.strip().split(">")
        l, p        = resto2.split("(")
        d[fase.strip()] = (w.strip(), l.strip(), float(p.replace("%)","")))
    return d

def resolve_choice(src, wins, losses):
    if src in elos:                   
        return src
    tag, mid = src[0], src[2:-1]      
    table = wins if tag=="W" else losses
    return table.get(mid)

# ─────────────── Utilitário de rebuild após undo ─────────────
def rebuild_from_choices(choices: dict, agenda: list):
    winners, losers = {}, {}
    prob = 1.0
    for mid, A, B in agenda:
        if mid not in choices:
            continue
        a = resolve_choice(A, winners, losers)
        b = resolve_choice(B, winners, losers)
        if not (a and b):  
            break
        vencedor           = choices[mid]
        perdedor           = b if vencedor == a else a
        winners[mid]       = vencedor
        losers[mid]        = perdedor
        pa = 1 / (1 + 10 ** ((elos[perdedor] - elos[vencedor]) / 400))
        prob *= pa if vencedor == a else (1 - pa)
    return winners, losers, prob

# ─────────────── Bracket com botões de download ──────────────
def plot_bracket(path_lines):
    info=parse_path(path_lines)
    fig,ax=plt.subplots(figsize=(13,7))
    ax.axis("off"); ax.set_xlim(-0.5,11); ax.set_ylim(-2.5,12)
    for lbl,(x,y) in PHASE_LABELS.items():
        ax.text(x+BOX_W/2, y, lbl, ha="center", weight="bold", fontsize=11)
    for mid,(x,y) in POS.items():
        if mid in info: draw_box(ax,x,y,*info[mid])
    st.pyplot(fig)
    for fmt,mime in [("png","image/png"),("pdf","application/pdf")]:
        buf=io.BytesIO(); fig.savefig(buf,format=fmt,bbox_inches="tight")
        st.download_button(f"Baixar bracket ({fmt.upper()})",
                           buf.getvalue(), file_name=f"bracket.{fmt}", mime=mime)
    plt.close(fig)

# ───────────── Estatísticas (gráfico + download) ─────────────
def estatisticas_fase(sim_por_perm=2000):
    times=df_elo.sort_values("elo_final",ascending=False)["time"].tolist()
    variaveis=["PRX","SEN","MIBR","TH"]
    perms=list(itertools.permutations(variaveis))
    tally={t:{"Semifinal":0,"Final":0,"Vencedor":0} for t in times}
    def p(a,b): return 1/(1+10**((elos[b]-elos[a])/400))
    def jogo(a,b): return a if random.random()<p(a,b) else b
    def sim(adv):
        f={t:"QF" for t in elos}
        uqf=[("G2",adv[0]),("XLG",adv[1]),("FNC",adv[2]),("RRQ",adv[3])]
        win,los=[],[]
        for a,b in uqf:
            w=jogo(a,b); l=b if w==a else a
            win.append(w); los.append(l)
        us1=jogo(win[0],win[1]); us2=jogo(win[2],win[3])
        f[us1]=f[us2]="Semifinal"
        uf=jogo(us1,us2); f[uf]="Final"
        lr1=jogo(los[0],los[1]); lr2=jogo(los[2],los[3])
        lr3=jogo(lr1,lr2); f[lr3]="Semifinal"
        lf=jogo(us1 if us1!=uf else us2, lr3); f[lf]="Final"
        gf=jogo(uf,lf); f[gf]="Vencedor"; return f
    with st.spinner("Simulando estatísticas…"):
        for perm in perms:
            for _ in range(sim_por_perm):
                fases=sim(perm)
                for t,fs in fases.items():
                    if fs=="Semifinal": tally[t]["Semifinal"] += 1
                    elif fs=="Final":
                        tally[t]["Semifinal"] += 1
                        tally[t]["Final"]     += 1
                    elif fs=="Vencedor":
                        tally[t]["Semifinal"] += 1
                        tally[t]["Final"]     += 1
                        tally[t]["Vencedor"]  += 1
    total = sim_por_perm * len(perms)
    df=pd.DataFrame(tally).T.div(total).mul(100).loc[times]

    fig,ax=plt.subplots(figsize=(12,6))
    df.plot(kind="bar",stacked=True,colormap="Set2",ax=ax)
    ax.set(title="Probabilidade de alcançar cada fase", ylabel="%", xlabel='')
    ax.grid(True,axis="y",ls="--",alpha=0.6)
    ax.set_xticks([])
    for i,team in enumerate(df.index):
        path=os.path.join(LOGOS,f"{team}.png")
        if os.path.exists(path):
            img=plt.imread(path)
            ax.add_artist(AnnotationBbox(OffsetImage(img,zoom=0.12),
                                         (i,-9.5),frameon=False,
                                         box_alignment=(0.5,0.5)))
        ax.text(i,-17.5,team,ha="center",va="top",fontsize=10)
    ax.set_ylim(-22,140); plt.tight_layout(); st.pyplot(fig)
    for fmt,mime in [("png","image/png"),("pdf","application/pdf")]:
        buf=io.BytesIO(); fig.savefig(buf,format=fmt,bbox_inches="tight")
        st.download_button(f"Baixar gráfico ({fmt.upper()})",
                           buf.getvalue(), file_name=f"estatisticas.{fmt}", mime=mime)
    plt.close(fig)

# ──────────────── Simulador campeonato ─────────────
def simulador_manual():
    st.header("Simulador de resultados")

    # ---- CSS para tooltips ----
    tooltip_css = """
    <style>
    .tooltip {position: relative; display: inline-block; cursor: help;}
    .tooltip .tooltiptext {
    visibility: hidden;
        width: 260px;
        background:#333; color:#fff; text-align:left; border-radius:6px;
        padding:6px; position:absolute; z-index:1; bottom:125%; left:50%;
        margin-left:-130px; opacity:0; transition:opacity .3s; font-size:0.8rem;
    }
    .tooltip:hover .tooltiptext {visibility:visible; opacity:1;}
    </style>
    """
    st.markdown(tooltip_css, unsafe_allow_html=True)

    # Seleção manual dos confrontos iniciais
    if "opponents" not in st.session_state:
        st.markdown("#### Selecione os 4 times que enfrentarão G2, XLG, FNC e RRQ")
        opcoes = ["PRX", "SEN", "MIBR", "TH"]
        selecao = []
        disponiveis = opcoes.copy()

        for i, cabeca in enumerate(["G2", "XLG", "FNC", "RRQ"]):
            escolha = st.selectbox(f"{cabeca} enfrenta:", [None] + disponiveis, key=f"opp_{i}")
            if escolha:
                selecao.append(escolha)
                disponiveis.remove(escolha)

        if len(selecao) == 4:
            if st.button("Confirmar confrontos iniciais"):
                st.session_state.opponents = selecao
                st.rerun()
        st.stop()

    opponents = st.session_state.opponents

    # ── Agenda fixa para simulador manual ────────────────────────
    AGENDA_MANUAL = [
        ("U1", "G2",  opponents[0]),
        ("U2", "XLG", opponents[1]),
        ("U3", "FNC", opponents[2]),
        ("U4", "RRQ", opponents[3]),
        ("U5", "W(U1)", "W(U2)"),
        ("U6", "W(U3)", "W(U4)"),
        ("L1", "L(U1)", "L(U2)"),
        ("L2", "L(U3)", "L(U4)"),
        ("L3", "W(L1)", "L(U5)"),
        ("L4", "W(L2)", "L(U6)"),
        ("L5", "W(L3)", "W(L4)"),
        ("U7", "W(U5)", "W(U6)"),
        ("L6", "W(L5)", "L(U7)"),
        ("GF", "W(U7)", "W(L6)")
    ]
    TOTAL_MATCHES = len(AGENDA_MANUAL)  # 14

    # ─────── Estado inicial ───────
    if "choices" not in st.session_state:
        st.session_state.choices  = {}
        st.session_state.winners  = {}
        st.session_state.losers   = {}
        st.session_state.prob     = 1.0
        st.session_state.order    = []
        st.session_state.last_increment = None

    # ─────── Progress bar ───────
    done = len(st.session_state.choices)
    st.markdown(f"**Progresso:** {done} / {TOTAL_MATCHES} partidas escolhidas")
    st.progress(done / TOTAL_MATCHES)

    # ─────── Botões auxiliares ───────
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Desfazer última escolha"):
            if st.session_state.order:
                last_mid = st.session_state.order.pop()
                st.session_state.choices.pop(last_mid, None)
                w, l, p = rebuild_from_choices(st.session_state.choices, AGENDA_MANUAL)
                st.session_state.winners = w
                st.session_state.losers  = l
                st.session_state.prob    = p
                st.session_state.last_increment = None
                st.rerun()
            else:
                st.info("Nenhuma escolha para desfazer.")
    with col2:
        if st.button("Recomeçar simulação"):
            for k in ("choices", "winners", "losers", "prob",
          "order", "opponents", "last_increment"):
                st.session_state.pop(k, None)
            st.rerun()


    # ─────── Loop das partidas ───────
    for mid, A, B in AGENDA_MANUAL:
        fase_nome = PHASE_DISPLAY[mid]

        if mid in st.session_state.choices:
            st.radio(f"{fase_nome}",
                     [st.session_state.choices[mid]], index=0, disabled=True)
            continue

        a = resolve_choice(A, st.session_state.winners, st.session_state.losers)
        b = resolve_choice(B, st.session_state.winners, st.session_state.losers)

        if not (a and b):
            st.radio(f"{fase_nome}: (aguardando…)", ["—"], index=0, disabled=True)
            continue

        # Probabilidade pré-jogo
        p_a = 1 / (1 + 10 ** ((elos[b] - elos[a]) / 400))
        p_b = 1 - p_a

        # texto mostrado no tooltip
        tip_a = f"p = 1 / (1 + 10^(({elos[b]} − {elos[a]}) / 400))"
        tip_b = f"p = 1 / (1 + 10^(({elos[a]} − {elos[b]}) / 400))"

        html = (
            "<b>Probabilidade:</b> "
            f"<span class='tooltip'>{a} {p_a*100:.1f}%"
            f"<span class='tooltiptext'>{tip_a}</span></span> × "
            f"<span class='tooltip'>{p_b*100:.1f}%"
            f"<span class='tooltiptext'>{tip_b}</span></span> {b}"
        )
        st.markdown(html, unsafe_allow_html=True)

        escolha = st.radio(f"{fase_nome}: {a} vs {b}", [a, b], key=f"opt_{mid}")
        if st.button(f"Confirmar {fase_nome}", key=f"btn_{mid}"):
            vencedor, perdedor = escolha, (b if escolha == a else a)

            prob_incr = p_a if vencedor == a else (1 - p_a)      # ← incremento

            st.session_state.choices[mid] = vencedor
            st.session_state.winners[mid] = vencedor
            st.session_state.losers[mid]  = perdedor
            st.session_state.order.append(mid)
            st.session_state.prob *= prob_incr
            st.session_state.last_increment = prob_incr           # ← salva
            st.rerun()

    inc = st.session_state.get("last_increment")
    if inc is not None:
        st.info(f"🔄 Incremento da última escolha: {inc * 100:.2f}%")


    st.success(f"Probabilidade do caminho: "
               f"{st.session_state.get('prob', 1) * 100:.4f}%")

# ─────────────────────────── Interface ───────────────────────
df, equipes = load_data()

with st.sidebar:
    aba = st.radio("📌 Seção", ["🏆 Caminhos e Bracket",
                                "📊 Estatísticas por fase",
                                "🧱​ Simulador manual"])

if aba == "🧱​ Simulador manual":
    simulador_manual()
    st.stop()

if aba == "📊 Estatísticas por fase":
    estatisticas_fase()
    st.stop()

# -------- Caminhos e bracket --------
with st.sidebar:
    escolha = st.selectbox("Equipe campeã", ["Todos"] + equipes)
    modo    = st.radio("Filtro de cenário",
                       ["Mais provável", "Menos provável", "Mostrar todos"])
    if modo == "Mostrar todos":
        ordem = st.radio("Ordenar por", ["Mais prováveis", "Menos prováveis"],
                         horizontal=True)
        qtde  = st.selectbox("Mostrar", [50, 100, 200, 300], index=0)
    else:
        ordem, qtde = None, 50

filtro = df if escolha == "Todos" else df[df["campeao_clean"] == escolha]
if modo == "Mais provável":
    filtro = filtro.nlargest(1, "probabilidade")
elif modo == "Menos provável":
    filtro = filtro.nsmallest(1, "probabilidade")
elif modo == "Mostrar todos":
    filtro = filtro.sort_values("probabilidade",
                                ascending=(ordem == "Menos prováveis"))

st.subheader(f"Caminhos encontrados: {len(filtro):,}")

for i, (_, row) in enumerate(filtro.head(qtde).iterrows(), 1):
    st.markdown(f"### 🏆 **{row['campeao']}** — {row['probabilidade']*100:.4f}%")
    st.code("\n".join(row["caminho"]))
    if st.button(f"📊 Ver bracket {i}", key=f"btn{i}"):
        plot_bracket(row["caminho"])
    st.markdown("---")
