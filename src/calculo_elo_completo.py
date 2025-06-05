
import pandas as pd
from collections import defaultdict

# Função de ELO esperado
def expected_score(elo_a, elo_b):
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

# Função para calcular delta de rounds total e verificar prorrogação
def calcular_delta_rounds(row):
    total_rounds_a = 0
    total_rounds_b = 0
    prorroga = False

    for i in range(1, 6):
        ra = row.get(f'rounds_time_a_mapa_{i}')
        rb = row.get(f'rounds_time_b_mapa_{i}')
        try:
            ra = float(ra)
            rb = float(rb)
        except:
            continue

        total_rounds_a += ra
        total_rounds_b += rb

        if (ra >= 13 and rb >= 12) or (rb >= 13 and ra >= 12):
            prorroga = True

    delta = abs(total_rounds_a - total_rounds_b)
    return delta, prorroga

# Lista dos 8 times do campeonato
times_campeonato = ['G2', 'XLG', 'FNC', 'RRQ', 'SEN', 'MIBR', 'PRX', 'TH']

# Ler arquivo CSV
df = pd.read_csv("data/modelo_partidas_vlrgg_bo5_exemplo.csv")
df['data'] = pd.to_datetime(df['data'], errors='coerce')
df = df.dropna(subset=['data'])
df = df.sort_values('data')

# Cálculo do ELO com K dinâmico
elo_ratings = defaultdict(lambda: 1500.0)
elo_history = []

for _, row in df.iterrows():
    team_a = row['time_a']
    team_b = row['time_b']
    winner = row['vencedor']

    if team_a not in times_campeonato and team_b not in times_campeonato:
        continue

    delta, prorroga = calcular_delta_rounds(row)

    if prorroga or delta < 10:
        k_dinamico = 16
    elif delta >= 25:
        k_dinamico = 48
    else:
        k_dinamico = 32

    elo_a = elo_ratings[team_a]
    elo_b = elo_ratings[team_b]

    expected_a = expected_score(elo_a, elo_b)
    score_a = 1 if winner == team_a else 0

    new_elo_a = elo_a + k_dinamico * (score_a - expected_a)
    new_elo_b = elo_b + k_dinamico * ((1 - score_a) - (1 - expected_a))

    elo_ratings[team_a] = new_elo_a
    elo_ratings[team_b] = new_elo_b

    elo_history.append({
        'data': row['data'],
        'team_a': team_a,
        'team_b': team_b,
        'winner': winner,
        'delta_rounds': delta,
        'prorroga': prorroga,
        'k_usado': k_dinamico,
        'elo_a_before': elo_a,
        'elo_b_before': elo_b,
        'elo_a_after': new_elo_a,
        'elo_b_after': new_elo_b
    })

# Gerar tabela final com os 8 times
elo_final = pd.DataFrame(
    [(team, elo_ratings[team]) for team in times_campeonato],
    columns=['time', 'elo_final']
).sort_values(by='elo_final', ascending=False)

# Salvar resultado
elo_final.to_csv("data/elo_final_campeonato.csv", index=False)
print(elo_final)
