# -*- coding: utf-8 -*-
"""
classificador_prioridade_crimes.py

Lê um CSV de ocorrências e adiciona duas colunas:
 - score_prioridade : pontuação numérica que indica gravidade/prioridade
 - prioridade        : categoria (Muito Alta / Alta / Média / Baixa)

Uso:
    python classificador_prioridade_crimes.py input.csv output.csv

Dependências:
    pip install pandas

Descrição da lógica (resumo):
 - usa tipo_crime e palavras-chave em descricao_modus_operandi para definir um peso base
 - adiciona pesos por arma utilizada, número de vítimas e suspeitos
 - ajusta a pontuação segundo o status_investigacao e termos do modus operandi
 - converte pontuação em 4 níveis de prioridade

O arquivo contém um dicionário DEFAULT_CONFIG para você ajustar pesos e limiares.
"""

from pathlib import Path
import sys
import re
import json
import pandas as pd
import numpy as np

# ------------------------- CONFIGURÁVEL -------------------------
DEFAULT_CONFIG = {
    # peso base por tipo de crime (valores exemplo — ajuste conforme necessidade)
    "crime_weight_map": {
        "homicídio": 100,
        "homicidio": 100,
        "homicide": 100,
        "estupro": 95,
        "sequestro": 90,
        "roubo": 70,
        "furto": 40,
        "fraude": 30,
        "arrombamento": 50,
        "outro": 20
    },

    # se descricao_modus_operandi contém uma dessas palavras, podemos sobrescrever/elevar
    "keyword_crime_weight_map": {
        "homicídio": 100,
        "homicidio": 100,
        "assassinato": 100,
        "estupro": 95,
        "sequestro": 90
    },

    # peso por arma
    "weapon_weight_map": {
        "arma de fogo": 40,
        "arma de fogo (outra)": 40,
        "faca": 25,
        "objeto contundente": 20,
        "nenhum": 0,
        "sem": 0
    },

    # pequenos acréscimos por termos do modus operandi (soma-se se múltiplos encontrarem)
    "modus_keyword_bonus": {
        "estupro": 10,
        "coletivo": 3,
        "golpe": 5,
        "fraude": 5,
        "invas\u00e3o": 5,
        "arrombamento": 5,
        "sequestro": 10
    },

    # valores por vítima / suspeito
    "victim_weight": 10,
    "suspect_weight": 5,

    # ajustes por status da investigação (podem reduzir ou aumentar a prioridade)
    "status_adj": {
        "arquivado": -30,
        "conclu\u00eddo": -10,
        "concluido": -10,
        "em andamento": 20,
        "aberto": 10,
        "pendente": 10
    },

    # limiares para converter score -> rótulo
    "thresholds": {
        "muito_alta": 120,
        "alta": 80,
        "media": 40
    }
}
# ----------------------- FIM CONFIGURÁVEL -----------------------


def clean_text(x):
    if pd.isna(x):
        return ""
    return str(x).lower()


def get_crime_weight(tipo_crime, descricao, cfg):
    tipo = clean_text(tipo_crime).strip()
    crime_map = cfg["crime_weight_map"]
    # tentativa direta por tipo
    base = None
    if tipo in crime_map:
        base = crime_map[tipo]
    else:
        # busca por aproximação (palavras-chave em tipo_crime)
        for k, v in crime_map.items():
            if k in tipo and k != "outro":
                base = v
                break
    if base is None:
        base = cfg["crime_weight_map"].get("outro", 20)

    # keywords na descricao podem indicar crime mais grave: usamos o maior entre base e keyword
    desc = clean_text(descricao)
    max_kw = 0
    for kw, w in cfg["keyword_crime_weight_map"].items():
        if kw in desc:
            max_kw = max(max_kw, w)
    return max(base, max_kw)


def get_weapon_weight(arma, cfg):
    a = clean_text(arma).strip()
    wm = cfg["weapon_weight_map"]
    # busca direta
    for k, v in wm.items():
        if k in a:
            return v
    # número/descrição desconhecida
    return 0


def modus_bonus(descricao, cfg):
    desc = clean_text(descricao)
    bonus = 0
    for k, v in cfg["modus_keyword_bonus"].items():
        if k in desc:
            bonus += v
    return bonus


def status_adjustment(status, cfg):
    s = clean_text(status).strip()
    for k, v in cfg["status_adj"].items():
        if k in s:
            return v
    return 0


def safe_int(x):
    try:
        if pd.isna(x):
            return 0
        # remove qualquer coisa não numérica
        return int(float(re.sub(r"[^0-9.-]", "", str(x))))
    except Exception:
        return 0


def score_row(row, cfg):
    tipo = row.get("tipo_crime", "")
    descricao = row.get("descricao_modus_operandi", "")
    arma = row.get("arma_utilizada", "")
    status = row.get("status_investigacao", "")

    crime_w = get_crime_weight(tipo, descricao, cfg)
    weapon_w = get_weapon_weight(arma, cfg)
    victims = safe_int(row.get("quantidade_vitimas", 0))
    suspects = safe_int(row.get("quantidade_suspeitos", 0))

    s = 0
    s += crime_w
    s += weapon_w
    s += victims * cfg["victim_weight"]
    s += suspects * cfg["suspect_weight"]
    s += modus_bonus(descricao, cfg)
    s += status_adjustment(status, cfg)

    # pequenas regras extras (opcionais)
    # se não há informação de arma, mas há muitos suspeitos e muitas vítimas, aumentar um pouco
    if weapon_w == 0 and victims >= 3 and suspects >= 2:
        s += 5

    # não deixar negativo
    if s < 0:
        s = 0
    return s


def score_to_label(score, cfg):
    t = cfg["thresholds"]
    if score >= t["muito_alta"]:
        return "Muito Alta"
    if score >= t["alta"]:
        return "Alta"
    if score >= t["media"]:
        return "Média"
    return "Baixa"


def classify_dataframe(df: pd.DataFrame, cfg=DEFAULT_CONFIG) -> pd.DataFrame:
    df = df.copy()

    # garantir colunas numéricas
    df["quantidade_vitimas"] = pd.to_numeric(df.get("quantidade_vitimas", 0), errors="coerce").fillna(0).astype(int)
    df["quantidade_suspeitos"] = pd.to_numeric(df.get("quantidade_suspeitos", 0), errors="coerce").fillna(0).astype(int)

    # aplicar
    df["score_prioridade"] = df.apply(lambda r: score_row(r, cfg), axis=1)
    df["prioridade"] = df["score_prioridade"].apply(lambda s: score_to_label(s, cfg))

    return df


def load_config_from_file(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        # mesclar (simples) — substitui chaves de topo
        cfg.update(user_cfg)
        return cfg
    except Exception:
        return DEFAULT_CONFIG


def main(argv):
    if len(argv) < 2:
        print("Uso: python classificador_prioridade_crimes.py input.csv [output.csv] [config.json]")
        return
    input_csv = Path(argv[1])
    output_csv = Path(argv[2]) if len(argv) >= 3 else input_csv.with_name(input_csv.stem + "_prioridade.csv")
    config_file = Path(argv[3]) if len(argv) >= 4 else None

    if not input_csv.exists():
        print(f"Arquivo não encontrado: {input_csv}")
        return

    cfg = DEFAULT_CONFIG
    if config_file and config_file.exists():
        cfg = load_config_from_file(config_file)
        print(f"Usando configuração de: {config_file}")

    df = pd.read_csv(input_csv)
    out = classify_dataframe(df, cfg)
    out.to_csv(output_csv, index=False)

    # resumo simples
    resumo = out["prioridade"].value_counts(dropna=False).to_dict()
    print("Arquivo salvo em:", output_csv)
    print("Resumo por prioridade:")
    for k, v in resumo.items():
        print(f"  {k}: {v}")
    


if __name__ == "__main__":
    main(sys.argv)
