
import pandas as pd
import random
import itertools
from collections import Counter

# Função de probabilidade baseada no ELO
def prob_vitoria(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

# Função para simular um confronto entre dois times
def simular_jogo(time_a, time_b):
    p = prob_vitoria(elos[time_a], elos[time_b])
    return time_a if random.random() < p else time_b

# Função para simular o campeonato com cabeças fixos e permutação de adversários
def simular_bracket_restrito(adversarios):
    uqf1 = simular_jogo('G2', adversarios[0])
    uqf2 = simular_jogo('XLG', adversarios[1])
    uqf3 = simular_jogo('FNC', adversarios[2])
    uqf4 = simular_jogo('RRQ', adversarios[3])

    usf1 = simular_jogo(uqf1, uqf2)
    usf2 = simular_jogo(uqf3, uqf4)
    uf = simular_jogo(usf1, usf2)

    lr1a = simular_jogo('G2' if uqf1 != 'G2' else adversarios[0],
                        'XLG' if uqf2 != 'XLG' else adversarios[1])
    lr1b = simular_jogo('FNC' if uqf3 != 'FNC' else adversarios[2],
                        'RRQ' if uqf4 != 'RRQ' else adversarios[3])

    lr2a = simular_jogo(uqf1 if uqf1 != usf1 else uqf2, lr1a)
    lr2b = simular_jogo(uqf3 if uqf3 != usf2 else uqf4, lr1b)

    lr3 = simular_jogo(lr2a, lr2b)
    lf = simular_jogo(usf1 if usf1 != uf else usf2, lr3)

    gf = simular_jogo(uf, lf)
    return gf

# =========================== INÍCIO ===========================

# Número de simulações por permutação
sim_por_bracket = 10000

# Carregar ELO do .csv
df_elo = pd.read_csv("data/elo_final_campeonato.csv")
elos = dict(zip(df_elo['time'], df_elo['elo_final']))

# Definir cabeças fixos e permutar os outros
times_fixos = ['G2', 'XLG', 'FNC', 'RRQ']
times_variaveis = ['PRX', 'SEN', 'MIBR', 'TH']
permutacoes_validas = list(itertools.permutations(times_variaveis))

# Ordenação para exibir
times_ordenados = df_elo.sort_values(by='elo_final', ascending=False)['time'].tolist()

# Simulações
contagem = Counter()
for perm in permutacoes_validas:
    for _ in range(sim_por_bracket):
        vencedor = simular_bracket_restrito(perm)
        contagem[vencedor] += 1

# Calcular probabilidades
total = sum(contagem.values())
probabilidades = {time: (contagem[time] / total) * 100 for time in times_ordenados}

# Exibir resultados
print("Probabilidade de cada time ser campeão (com cabeças fixos):")
for time, prob in sorted(probabilidades.items(), key=lambda x: x[1], reverse=True):
    print(f"{time}: {prob:.2f}%")
