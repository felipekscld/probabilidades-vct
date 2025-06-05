
import pandas as pd
import random
import itertools
from collections import Counter
import matplotlib.pyplot as plt

def prob_vitoria(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def simular_jogo(time_a, time_b):
    p = prob_vitoria(elos[time_a], elos[time_b])
    return time_a if random.random() < p else time_b

def simular_bracket_com_fases(adversarios):
    fases = {t: 'QF' for t in elos}
    uqf1_loser = 'G2' if simular_jogo('G2', adversarios[0]) != 'G2' else adversarios[0]
    uqf2_loser = 'XLG' if simular_jogo('XLG', adversarios[1]) != 'XLG' else adversarios[1]
    uqf3_loser = 'FNC' if simular_jogo('FNC', adversarios[2]) != 'FNC' else adversarios[2]
    uqf4_loser = 'RRQ' if simular_jogo('RRQ', adversarios[3]) != 'RRQ' else adversarios[3]

    uqf1 = 'G2' if uqf1_loser != 'G2' else adversarios[0]
    uqf2 = 'XLG' if uqf2_loser != 'XLG' else adversarios[1]
    uqf3 = 'FNC' if uqf3_loser != 'FNC' else adversarios[2]
    uqf4 = 'RRQ' if uqf4_loser != 'RRQ' else adversarios[3]

    usf1 = simular_jogo(uqf1, uqf2)
    usf2 = simular_jogo(uqf3, uqf4)
    fases[usf1] = 'SF'
    fases[usf2] = 'SF'

    uf = simular_jogo(usf1, usf2)
    fases[uf] = 'Final'

    lr1a = simular_jogo(uqf1_loser, uqf2_loser)
    lr1b = simular_jogo(uqf3_loser, uqf4_loser)

    lr2a = simular_jogo(uqf1 if uqf1 != usf1 else uqf2, lr1a)
    lr2b = simular_jogo(uqf3 if uqf3 != usf2 else uqf4, lr1b)

    lr3 = simular_jogo(lr2a, lr2b)
    fases[lr3] = 'Semifinal'

    lf = simular_jogo(usf1 if usf1 != uf else usf2, lr3)
    fases[lf] = 'Final'

    gf = simular_jogo(uf, lf)
    fases[gf] = 'Vencedor'

    return fases

# ========================== INÍCIO ===========================

sim_por_perm = 10000

df_elo = pd.read_csv("data/elo_final_campeonato.csv")
elos = dict(zip(df_elo['time'], df_elo['elo_final']))
times_ordenados = df_elo.sort_values(by='elo_final', ascending=False)['time'].tolist()

# Cabeças fixos e permutáveis
fixos = ['G2', 'XLG', 'FNC', 'RRQ']
variaveis = ['PRX', 'SEN', 'MIBR', 'TH']
permutacoes = list(itertools.permutations(variaveis))

# Contagem de fases
fases_por_time = {t: {'Semifinal': 0, 'Final': 0, 'Vencedor': 0} for t in times_ordenados}

for perm in permutacoes:
    for _ in range(sim_por_perm):
        fases = simular_bracket_com_fases(perm)
        for t in fases:
            if fases[t] == 'Semifinal':
                fases_por_time[t]['Semifinal'] += 1
            elif fases[t] == 'Final':
                fases_por_time[t]['Semifinal'] += 1
                fases_por_time[t]['Final'] += 1
            elif fases[t] == 'Vencedor':
                fases_por_time[t]['Semifinal'] += 1
                fases_por_time[t]['Final'] += 1
                fases_por_time[t]['Vencedor'] += 1

# Converter para DataFrame
df_fases = pd.DataFrame.from_dict(fases_por_time, orient='index')
df_fases = df_fases.div(sim_por_perm * len(permutacoes)).multiply(100)
df_fases = df_fases.loc[times_ordenados]

# Gráfico
ax = df_fases.plot(kind='bar', stacked=True, figsize=(12, 6), colormap='Set2')
plt.title('Probabilidade de alcançar cada fase')
plt.ylabel('%')
plt.xlabel('Equipe')
plt.xticks(rotation=0)
plt.legend(title='Fase')
plt.tight_layout()
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.show()
