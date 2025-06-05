import json
import re
import pandas as pd
from pathlib import Path

JSON_IN   = Path("caminhos_campeonato.json")       
PARQUET_O = Path("caminhos.parquet")    

TEAM_RE   = re.compile(r"\b([A-Z][A-Z0-9]{1,4})\s*>\s*([A-Z][A-Z0-9]{1,4})")

print("Lendo JSON...")
with JSON_IN.open(encoding="utf-8") as f:
    dados = json.load(f)

def extrai_times(lista_jogos):
    """Retorna set com os dois times de cada linha 'A > B'."""
    s = set()
    for jogo in lista_jogos:
        m = TEAM_RE.search(jogo)
        if m:
            s.update(m.groups())        
    return list(s)

print("Processando…")
for d in dados:
    d["times_participantes"] = extrai_times(d["caminho"])

print("Escrevendo parquet…")
df = pd.DataFrame(dados)
df.to_parquet(PARQUET_O, index=False)
print(f"Arquivo salvo: {PARQUET_O}  ({len(df):,} linhas)")
