"""
Coleta diária dos dados do CBLOW e gravação em SQLite.

Como funciona:
1. Baixa a lista de partidas (/matches).
2. Para cada partida FINALIZADA que ainda não tem detalhes no banco,
   baixa /matches/ID e grava jogos + estatísticas por jogador.
3. Partidas já coletadas não são baixadas de novo.

Rode com:  python coleta_cblow.py
Dependência: pip install requests
"""

import json
import sqlite3
import time
from datetime import datetime, timezone

import requests

BASE = "https://api.cblow.xyz"
ARQUIVO_BANCO = "cblow.db"
PAUSA_SEGUNDOS = 1.0  # pausa entre chamadas, para não pesar no servidor


def buscar_json(caminho):
    """Faz o GET em uma rota da API e devolve o JSON."""
    resposta = requests.get(f"{BASE}/{caminho}", timeout=30)
    resposta.raise_for_status()
    return resposta.json()


def criar_tabelas(con):
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS times (
            id INTEGER PRIMARY KEY,
            slug TEXT,
            nome TEXT,
            tag TEXT
        );

        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY,
            slug TEXT,
            nick TEXT,
            role TEXT,
            time_id INTEGER
        );

        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY,
            fase TEXT,
            melhor_de INTEGER,
            status TEXT,
            agendada_em TEXT,
            time1_id INTEGER,
            time2_id INTEGER,
            placar1 INTEGER,
            placar2 INTEGER
        );

        CREATE TABLE IF NOT EXISTS jogos (
            partida_id INTEGER,
            numero INTEGER,
            vencedor_id INTEGER,
            lado_azul_id INTEGER,
            duracao_seg INTEGER,
            objetivos_time1 TEXT,
            objetivos_time2 TEXT,
            PRIMARY KEY (partida_id, numero)
        );

        CREATE TABLE IF NOT EXISTS stats_jogo (
            partida_id INTEGER,
            jogo_numero INTEGER,
            jogador_id INTEGER,
            time_id INTEGER,
            campeao TEXT,
            kills INTEGER,
            deaths INTEGER,
            assists INTEGER,
            cs INTEGER,
            PRIMARY KEY (partida_id, jogo_numero, jogador_id)
        );

        -- Guarda o JSON original de cada partida, para reprocessar se precisar
        CREATE TABLE IF NOT EXISTS bruto_partidas (
            partida_id INTEGER PRIMARY KEY,
            coletado_em TEXT,
            json TEXT
        );
        """
    )


def salvar_time(con, t):
    con.execute(
        "INSERT OR REPLACE INTO times (id, slug, nome, tag) VALUES (?, ?, ?, ?)",
        (t["id"], t.get("slug"), t.get("name"), t.get("tag")),
    )


def salvar_partida(con, m):
    salvar_time(con, m["team1"])
    salvar_time(con, m["team2"])
    con.execute(
        """INSERT OR REPLACE INTO partidas
           (id, fase, melhor_de, status, agendada_em,
            time1_id, time2_id, placar1, placar2)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            m["id"], m.get("stage"), m.get("bestOf"), m.get("status"),
            m.get("scheduledAt"), m["team1"]["id"], m["team2"]["id"],
            m.get("team1Score"), m.get("team2Score"),
        ),
    )


def salvar_detalhes(con, detalhe):
    partida_id = detalhe["id"]

    for jogo in detalhe.get("games", []):
        con.execute(
            """INSERT OR REPLACE INTO jogos
               (partida_id, numero, vencedor_id, lado_azul_id, duracao_seg,
                objetivos_time1, objetivos_time2)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                partida_id, jogo["number"], jogo.get("winnerId"),
                jogo.get("blueId"), jogo.get("durationSec"),
                json.dumps(jogo.get("objectives1")),
                json.dumps(jogo.get("objectives2")),
            ),
        )

        for linha in jogo.get("lines", []):
            j = linha["player"]
            con.execute(
                """INSERT OR REPLACE INTO jogadores
                   (id, slug, nick, role, time_id) VALUES (?, ?, ?, ?, ?)""",
                (j["id"], j.get("slug"), j.get("nick"), j.get("role"),
                 linha.get("teamId")),
            )
            con.execute(
                """INSERT OR REPLACE INTO stats_jogo
                   (partida_id, jogo_numero, jogador_id, time_id, campeao,
                    kills, deaths, assists, cs)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    partida_id, jogo["number"], j["id"], linha.get("teamId"),
                    linha.get("champion"), linha.get("kills"),
                    linha.get("deaths"), linha.get("assists"), linha.get("cs"),
                ),
            )

    con.execute(
        "INSERT OR REPLACE INTO bruto_partidas VALUES (?, ?, ?)",
        (
            partida_id,
            datetime.now(timezone.utc).isoformat(),
            json.dumps(detalhe, ensure_ascii=False),
        ),
    )


def partida_ja_tem_detalhes(con, partida_id):
    linha = con.execute(
        "SELECT 1 FROM jogos WHERE partida_id = ? LIMIT 1", (partida_id,)
    ).fetchone()
    return linha is not None


def main():
    con = sqlite3.connect(ARQUIVO_BANCO)
    criar_tabelas(con)

    partidas = buscar_json("matches")
    if not isinstance(partidas, list):
        raise SystemExit(f"Formato inesperado em /matches: {type(partidas)}")

    print(f"{len(partidas)} partidas na lista.")
    novas = 0

    for m in partidas:
        salvar_partida(con, m)

        if m.get("status") == "finalizada" and not partida_ja_tem_detalhes(con, m["id"]):
            time.sleep(PAUSA_SEGUNDOS)
            try:
                detalhe = buscar_json(f"matches/{m['id']}")
                salvar_detalhes(con, detalhe)
                novas += 1
                print(f"  Partida {m['id']}: detalhes salvos.")
            except Exception as erro:
                # Não derruba a coleta toda por causa de uma partida
                print(f"  Partida {m['id']}: erro ({erro}). Tentaremos de novo amanhã.")

    con.commit()
    con.close()
    print(f"Pronto. {novas} partidas novas com detalhes.")


if __name__ == "__main__":
    main()