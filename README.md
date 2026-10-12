# 📊 Dicionário de Dados - Banco do CBLOW (`cblow.db`)

Este banco de dados relacional (SQLite) armazena informações de partidas, times, jogadores e desempenho individual do campeonato comunitário CBLOW.

---

## 🔗 Diagrama de Relacionamento (DER)

- **`times`** (1) ─── (N) **`jogadores`**
- **`times`** (1) ─── (N) **`partidas`** (como `time1_id` e `time2_id`)
- **`partidas`** (1) ─── (N) **`jogos`**
- **`jogos`** (1) ─── (N) **`stats_jogo`** (via `partida_id` + `jogo_numero`)
- **`jogadores`** (1) ─── (N) **`stats_jogo`**

---

## 📋 Tabelas e Campos

### 1. `times`
Armazena as 8 equipes participantes do campeonato.

| Campo | Tipo SQL | Chaves / Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **PK** | Identificador único da equipe na API do CBLOW. |
| `slug` | `TEXT` | | Nome curto simplificado para URLs (ex: `pain-gaming`). |
| `nome` | `TEXT` | | Nome oficial completo da equipe. |
| `tag` | `TEXT` | | Sigla de 3 a 4 letras que representa o time (ex: `PNG`, `LOUD`). |

---

### 2. `jogadores`
Armazena o cadastro dos 64 jogadores vinculados às suas equipes.

| Campo | Tipo SQL | Chaves / Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **PK** | Identificador único do jogador na API. |
| `slug` | `TEXT` | | Nome simplificado para URLs. |
| `nick` | `TEXT` | | Nickname/nome de invocador do jogador. |
| `role` | `TEXT` | | Posição no jogo (`TOP`, `JNG`, `MID`, `ADC`, `SUP`). |
| `time_id` | `INTEGER` | **FK** (`times.id`) | ID da equipe que o jogador defende no campeonato. |

---

### 3. `partidas`
Registra a série/confronto agendado entre duas equipes (MD1, MD3 ou MD5).

| Campo | Tipo SQL | Chaves / Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | **PK** | Identificador único do confronto na API. |
| `fase` | `TEXT` | | Etapa do torneio (ex: `Fase de Grupos`, `Playoffs`, `Final`). |
| `melhor_de` | `INTEGER` | | Quantidade máxima de jogos na série (`1`, `3` ou `5`). |
| `status` | `TEXT` | | Estado atual da partida (`agendada`, `em_andamento`, `finalizada`). |
| `agendada_em` | `TEXT` | | Data/hora agendada no formato ISO-8601 UTC (ex: `2026-10-15T18:00:00Z`). |
| `time1_id` | `INTEGER` | **FK** (`times.id`) | ID da primeira equipe do confronto. |
| `time2_id` | `INTEGER` | **FK** (`times.id`) | ID da segunda equipe do confronto. |
| `placar1` | `INTEGER` | | Vitórias acumuladas do Time 1 na série. |
| `placar2` | `INTEGER` | | Vitórias acumuladas do Time 2 na série. |

---

### 4. `jogos`
Registra cada mapa/partida individual disputado dentro de uma série.

| Campo | Tipo SQL | Chaves / Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `partida_id` | `INTEGER` | **PK, FK** (`partidas.id`) | ID da série/confronto a que o jogo pertence. |
| `numero` | `INTEGER` | **PK** | Sequencial do jogo na série (`1` para Jogo 1, `2` para Jogo 2, etc.). |
| `vencedor_id` | `INTEGER` | **FK** (`times.id`) | ID da equipe vencedora deste mapa. |
| `lado_azul_id` | `INTEGER` | **FK** (`times.id`) | ID da equipe que jogou no Lado Azul (*Blue Side*). |
| `duracao_seg` | `INTEGER` | | Duração total do jogo em segundos. |
| `objetivos_time1` | `TEXT` | JSON | Dados estruturados em JSON de abates de Barão, Dragão, Arauto e Torres (Time 1). |
| `objetivos_time2` | `TEXT` | JSON | Dados estruturados em JSON de abates de objetivos (Time 2). |

---

### 5. `stats_jogo`
Registra o desempenho estatístico individual de cada jogador por partida jogada.

| Campo | Tipo SQL | Chaves / Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `partida_id` | `INTEGER` | **PK, FK** (`jogos.partida_id`) | ID do confronto a que o jogo pertence. |
| `jogo_numero` | `INTEGER` | **PK, FK** (`jogos.numero`) | Número do jogo dentro da série. |
| `jogador_id` | `INTEGER` | **PK, FK** (`jogadores.id`) | ID do jogador a quem pertencem os números. |
| `time_id` | `INTEGER` | **FK** (`times.id`) | ID do time defendido pelo jogador no jogo. |
| `campeao` | `TEXT` | | Nome do campeão utilizado pelo jogador (ex: `Ahri`, `Lee Sin`). |
| `kills` | `INTEGER` | | Total de abates/assassinatos efetuados pelo jogador. |
| `deaths` | `INTEGER` | | Total de mortes sofridas pelo jogador. |
| `assists` | `INTEGER` | | Total de assistências em abates. |
| `cs` | `INTEGER` | | *Creep Score* (tropas de rota + monstros da selva abatidos). |

---

### 6. `bruto_partidas`
Tabela técnica de backup para preservar as respostas brutas retornadas pela API.

| Campo | Tipo SQL | Chaves / Restrições | Descrição |
| :--- | :--- | :--- | :--- |
| `partida_id` | `INTEGER` | **PK** | ID da partida coletada. |
| `coletado_em` | `TEXT` | | Data/hora em UTC no momento em que o JSON foi salvo no banco. |
| `json` | `TEXT` | JSON | Payload completo sem alterações retornado pela rota `/matches/{id}`. |