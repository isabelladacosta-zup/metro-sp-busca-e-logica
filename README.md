# 🚇 Metrô de SP — Busca (BFS/DFS) + Lógica Proposicional/Predicados

Projeto que modela a rede das linhas 1 (Azul), 2 (Verde) e 3 (Vermelha) do
Metrô de São Paulo como um grafo, usa **busca em grafos** (BFS, DFS,
Dijkstra) para planejar viagens e uma **base de conhecimento em lógica de
predicados** para inferir o impacto de estações fechadas na rede.

| Linha | Cor | Trecho |
|---|---|---|
| 1 | Azul `#0B4EA2` | Tucuruvi ↔ Jabaquara |
| 2 | Verde `#007E5E` | Vila Madalena ↔ Vila Prudente |
| 3 | Vermelha `#EE1C25` | Palmeiras-Barra Funda ↔ Corinthians-Itaquera |

Estações de integração: **Sé** (1×3), **Paraíso** (1×2), **Ana Rosa** (1×2).

## Conteúdo do repositório

| Arquivo | Descrição |
|---|---|
| `metro_sp_busca_e_logica.ipynb` | Notebook Jupyter com todo o desenvolvimento, explicações e a bateria de testes |
| `metro_sp_busca_e_logica.py` | Mesmo conteúdo do notebook em formato de script Python (`# %%` = célula) |
| `app_metro.html` | Versão web interativa, em HTML/JS puro, sem servidor nem dependências — abre direto no navegador |

## Como o projeto está organizado

### 1. Modelagem da rede (grafo)

Cada linha é uma sequência ordenada de estações. `construir_mapa()` gera um
grafo não-dirigido `estação -> {(vizinho, linha), ...}`, onde cada aresta
carrega a linha à qual pertence — necessário porque duas estações vizinhas
podem estar conectadas por mais de uma linha (ex.: Sé/Paraíso/Ana Rosa).

### 2. Base de conhecimento (lógica de predicados)

Os fatos são representados como tuplas atômicas:

- `pertence(estação, linha)` — a estação faz parte da linha
- `conecta(a, b, linha)` — trecho físico entre duas estações
- `terminal(estação, linha)` — a estação é ponta da linha
- `fechada(estação)` — fato dinâmico, injetado por cenário (ex.: interdição)

`inferir()` aplica encadeamento para frente sobre essas regras:

| Regra | Leitura |
|---|---|
| **R1** | `aberta(E) ← pertence(E, L) ∧ ¬fechada(E)` |
| **R2** | `operante(A,B,L) ← conecta(A,B,L) ∧ aberta(A) ∧ aberta(B)` |
| **R3** | `serve(L,E) ← pertence(E,L)` |
| **R6** | `integracao(E) ← pertence(E,L₁) ∧ pertence(E,L₂) ∧ L₁≠L₂ ∧ aberta(E)` |
| **R7** | `linha_cortada(L) ← fechada(E) ∧ pertence(E,L) ∧ ¬terminal(E,L)` |
| **R8** | `isoladas(L₁,L₂) ← ¬∃E : integracao(E) ∧ pertence(E,L₁) ∧ pertence(E,L₂)` |

A regra **R7** é a que explica, por exemplo, por que fechar **Paraíso**
parte a Linha 2 em dois pedaços: Paraíso não é terminal dela, então a linha
deixa de ser percorrível de ponta a ponta.

### 3. Busca de rotas

- **BFS** (`bfs_rota`) — encontra o caminho com **menor número de paradas**.
- **DFS** (`dfs_rota`) — encontra *uma* rota válida, não necessariamente a
  menor; serve para comparar esforço de busca com a BFS.
- **Dijkstra (bônus)** — duas variações que tratam o estado da busca como
  `(estação, linha_atual)`:
  - `menos_baldeacoes_rota`: custo 0 por trecho, custo 1 por troca de linha.
  - `rota_mais_rapida`: custo 2 min por trecho, +5 min por baldeação.

Todas as buscas respeitam a lista de estações fechadas (uma estação fechada
não pode ser usada nem como parada intermediária).

Ao longo do caminho encontrado, `marcar_baldeacoes()` detecta onde a linha
de chegada muda em relação à linha de saída e anota isso como baldeação.

### 4. Interpretação de linguagem natural

`interpretar_pedido()` entende frases livres em português, por exemplo:

```
"de Vila Prudente para Jabaquara com a estação Paraíso interditada"
```

Ele extrai origem, destino e estações fechadas, tolerando acentos e
pequenos erros de digitação via `difflib` (correspondência aproximada de
nomes de estação).

### 5. Narração e mapa visual

- `narrar()` transforma o resultado da busca em um texto legível, com
  trecho por linha, avisos de baldeação e o motivo caso não haja rota
  (linha cortada por interdição ou falta de integração).
- `mapa_html()` desenha as três linhas com as cores oficiais, destacando a
  rota, as baldeações (⇄) e as estações fechadas (⛔).

### 6. Painel interativo (Jupyter)

`painel()` monta uma interface com `ipywidgets` (dropdowns de origem/
destino, seleção de estações fechadas, escolha de estratégia de busca e
campo de texto livre) — só funciona dentro de um Jupyter Notebook/Lab.

### 7. Bateria de testes

`rodar_testes()` valida 8 cenários (6 obrigatórios + 2 do grupo), cobrindo
rota simples, múltiplas baldeações, estação fechada que corta uma linha e
estação fechada que não impede a viagem. Todos os 8 casos passam.

## Como rodar

### Opção 1 — Jupyter Notebook (com painel interativo)

```bash
pip install jupyter notebook ipywidgets
jupyter notebook
```

Abra `metro_sp_busca_e_logica.ipynb` e execute as células em ordem.

### Opção 2 — Script Python (sem interface, só os testes/demonstração)

```bash
python metro_sp_busca_e_logica.py
```

### Opção 3 — App web (HTML/JS puro, sem servidor)

Basta abrir `app_metro.html` diretamente no navegador (duplo clique). Toda
a lógica de busca, inferência e interpretação de pedido foi portada para
JavaScript, então funciona offline, sem instalar nada.
