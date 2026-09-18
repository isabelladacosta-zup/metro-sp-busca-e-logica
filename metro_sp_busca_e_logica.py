# %% [markdown]
# # Metrô de SP — Busca (BFS/DFS) + Lógica Proposicional/Predicados
#
# **TODO 4 a 10 resolvidos.**
#
# | Linha | Cor | Trecho |
# |---|---|---|
# | 1 | Azul `#0B4EA2` | Tucuruvi ↔ Jabaquara |
# | 2 | Verde `#007E5E` | Vila Madalena ↔ Vila Prudente |
# | 3 | Vermelha `#EE1C25` | Palmeiras-Barra Funda ↔ Corinthians-Itaquera |
#
# Estações de integração: **Sé** (1×3), **Paraíso** (1×2), **Ana Rosa** (1×2).

# %%
from collections import deque, defaultdict
import heapq
import re
import unicodedata
import difflib

# ---------------------------------------------------------------- dados base
CORES = {
    "Linha 1": "#0B4EA2",   # azul
    "Linha 2": "#007E5E",   # verde
    "Linha 3": "#EE1C25",   # vermelha
}

NOMES_LINHA = {
    "Linha 1": "Linha 1 - Azul",
    "Linha 2": "Linha 2 - Verde",
    "Linha 3": "Linha 3 - Vermelha",
}

LINHAS = {
    "Linha 1": [
        "Tucuruvi", "Parada Inglesa", "Jardim São Paulo-Ayrton Senna", "Santana",
        "Carandiru", "Portuguesa-Tietê", "Armênia", "Tiradentes", "Luz",
        "São Bento", "Sé", "Liberdade", "São Joaquim", "Vergueiro", "Paraíso",
        "Ana Rosa", "Vila Mariana", "Santa Cruz", "Praça da Árvore", "Saúde",
        "São Judas", "Conceição", "Jabaquara",
    ],
    "Linha 2": [
        "Vila Madalena", "Sumaré", "Clínicas", "Consolação", "Trianon-Masp",
        "Brigadeiro", "Paraíso", "Ana Rosa", "Chácara Klabin",
        "Santos-Imigrantes", "Alto do Ipiranga", "Sacomã", "Tamanduateí",
        "Vila Prudente",
    ],
    "Linha 3": [
        "Palmeiras-Barra Funda", "Marechal Deodoro", "Santa Cecília",
        "República", "Anhangabaú", "Sé", "Pedro II", "Brás", "Bresser-Mooca",
        "Belém", "Tatuapé", "Carrão", "Penha", "Vila Matilde",
        "Guilhermina-Esperança", "Patriarca", "Artur Alvim",
        "Corinthians-Itaquera",
    ],
}

ESTACOES = sorted({e for seq in LINHAS.values() for e in seq})


def construir_mapa():
    """Grafo não-dirigido: estação -> {(vizinho, linha), ...}."""
    mapa = defaultdict(set)
    for linha, seq in LINHAS.items():
        for a, b in zip(seq, seq[1:]):
            mapa[a].add((b, linha))
            mapa[b].add((a, linha))
    return dict(mapa)


MAPA = construir_mapa()

print(f"{len(ESTACOES)} estações distintas, "
      f"{sum(len(v) for v in MAPA.values()) // 2} trechos.")

# %% [markdown]
# ## TODO 5 — `fatos_base()`
#
# Base de conhecimento em forma de predicados (tuplas):
#
# * `pertence(estacao, linha)` — estação faz parte da linha
# * `conecta(a, b, linha)` — trecho físico entre duas estações
# * `terminal(estacao, linha)` — ponta da linha
# * `fechada(estacao)` — fato dinâmico, injetado pelo cenário

# %%
def fatos_base(fechadas=()):
    """Devolve o conjunto de fatos atômicos da base de conhecimento."""
    fatos = set()
    for linha, seq in LINHAS.items():
        for est in seq:
            fatos.add(("pertence", est, linha))
        fatos.add(("terminal", seq[0], linha))
        fatos.add(("terminal", seq[-1], linha))
        for a, b in zip(seq, seq[1:]):
            fatos.add(("conecta", a, b, linha))
            fatos.add(("conecta", b, a, linha))
    for est in fechadas:
        fatos.add(("fechada", est))
    return fatos


_f = fatos_base()
print(f"{len(_f)} fatos na base ("
      f"{sum(1 for x in _f if x[0] == 'pertence')} pertence, "
      f"{sum(1 for x in _f if x[0] == 'conecta')} conecta).")

# %% [markdown]
# ## TODO 6 e 7 — regras de inferência
#
# | Regra | Leitura |
# |---|---|
# | **R1** | `aberta(E) ← pertence(E, L) ∧ ¬fechada(E)` |
# | **R2** | `operante(A,B,L) ← conecta(A,B,L) ∧ aberta(A) ∧ aberta(B)` |
# | **R3** | `serve(L,E) ← pertence(E,L)` |
# | **R6** | `integracao(E) ← pertence(E,L₁) ∧ pertence(E,L₂) ∧ L₁≠L₂ ∧ aberta(E)` |
# | **R7** *(do grupo)* | `linha_cortada(L) ← fechada(E) ∧ pertence(E,L) ∧ ¬terminal(E,L)` |
# | **R8** *(do grupo)* | `isoladas(L₁,L₂) ← ¬∃E : integracao(E) ∧ pertence(E,L₁) ∧ pertence(E,L₂)` |
#
# R7 é o que explica o cenário 5: fechar **Paraíso** parte a Linha 2 em dois
# pedaços, porque Paraíso não é terminal dela.

# %%
def inferir(fatos):
    """Encadeamento para frente: aplica R1..R8 até não gerar mais nada."""
    derivados = set()

    fechadas = {f[1] for f in fatos if f[0] == "fechada"}
    pertence = defaultdict(set)          # estação -> {linhas}
    for f in fatos:
        if f[0] == "pertence":
            pertence[f[1]].add(f[2])
    terminais = {(f[1], f[2]) for f in fatos if f[0] == "terminal"}

    # R1 — aberta
    for est in pertence:
        if est not in fechadas:
            derivados.add(("aberta", est))
    abertas = {f[1] for f in derivados if f[0] == "aberta"}

    # R2 — operante
    for f in fatos:
        if f[0] == "conecta" and f[1] in abertas and f[2] in abertas:
            derivados.add(("operante", f[1], f[2], f[3]))

    # R3 — serve
    for est, linhas in pertence.items():
        for linha in linhas:
            derivados.add(("serve", linha, est))

    # R6 — integração
    for est, linhas in pertence.items():
        if len(linhas) >= 2 and est in abertas:
            derivados.add(("integracao", est))
            for l1 in sorted(linhas):
                for l2 in sorted(linhas):
                    if l1 < l2:
                        derivados.add(("integra", est, l1, l2))

    # R7 — linha cortada (regra do grupo)
    for est in fechadas:
        for linha in pertence.get(est, ()):
            if (est, linha) not in terminais:
                derivados.add(("linha_cortada", linha))

    # R8 — par de linhas sem integração viável (regra do grupo)
    todas = sorted(LINHAS)
    for i, l1 in enumerate(todas):
        for l2 in todas[i + 1:]:
            if not any(("integra", e, l1, l2) in derivados for e in pertence):
                derivados.add(("isoladas", l1, l2))

    return fatos | derivados


def consultar(kb, predicado):
    """Filtra a base já inferida por nome de predicado."""
    return sorted(f for f in kb if f[0] == predicado)


kb = inferir(fatos_base())
print("Integrações:", [f[1] for f in consultar(kb, "integracao")])
print("Cortadas:", consultar(kb, "linha_cortada"))

kb_p = inferir(fatos_base(fechadas={"Paraíso"}))
print("\nCom Paraíso fechada →")
print("  integrações:", [f[1] for f in consultar(kb_p, "integracao")])
print("  cortadas   :", [f[1] for f in consultar(kb_p, "linha_cortada")])

# %% [markdown]
# ## TODO 4 — busca (BFS e DFS) com anotação de baldeação
#
# A BFS devolve o caminho com **menor número de paradas**; percorrendo o
# caminho, sempre que a linha do trecho de chegada muda para a linha do
# trecho seguinte, anota-se uma **baldeação** naquela estação.

# %%
def vizinhos(estacao, fechadas=frozenset()):
    """Vizinhos operantes (R2): o trecho só vale se as duas pontas abrem."""
    return sorted((v, l) for v, l in MAPA.get(estacao, ()) if v not in fechadas)


def _reconstruir(veio, destino):
    """veio: estação -> (anterior, linha_usada). Devolve [(estação, linha)]."""
    caminho = []
    atual = destino
    while atual is not None:
        anterior, linha = veio[atual]
        caminho.append((atual, linha))
        atual = anterior
    caminho.reverse()
    return caminho


def marcar_baldeacoes(caminho):
    """Anota a baldeação na estação onde a troca de linha acontece."""
    baldeacoes = []
    for i in range(1, len(caminho) - 1):
        linha_chegada = caminho[i][1]
        linha_saida = caminho[i + 1][1]
        if linha_chegada != linha_saida:
            baldeacoes.append((caminho[i][0], linha_chegada, linha_saida))
    return baldeacoes


def bfs_rota(origem, destino, fechadas=frozenset()):
    """BFS por menor número de paradas. -> (caminho | None, visitadas)."""
    fechadas = set(fechadas)
    visitadas = []
    if origem in fechadas or destino in fechadas:
        return None, visitadas

    veio = {origem: (None, None)}
    fila = deque([origem])
    while fila:
        atual = fila.popleft()
        visitadas.append(atual)
        if atual == destino:
            return _reconstruir(veio, destino), visitadas
        for viz, linha in vizinhos(atual, fechadas):
            if viz not in veio:
                veio[viz] = (atual, linha)
                fila.append(viz)
    return None, visitadas


def dfs_rota(origem, destino, fechadas=frozenset()):
    """DFS iterativa — acha *uma* rota, não necessariamente a menor."""
    fechadas = set(fechadas)
    visitadas = []
    if origem in fechadas or destino in fechadas:
        return None, visitadas

    veio = {origem: (None, None)}
    pilha = [origem]
    vistos = set()
    while pilha:
        atual = pilha.pop()
        if atual in vistos:
            continue
        vistos.add(atual)
        visitadas.append(atual)
        if atual == destino:
            return _reconstruir(veio, destino), visitadas
        for viz, linha in reversed(vizinhos(atual, fechadas)):
            if viz not in vistos:
                veio.setdefault(viz, (atual, linha))
                if viz not in veio or veio[viz][0] is None:
                    pass
                veio[viz] = (atual, linha)
                pilha.append(viz)
    return None, visitadas

# %% [markdown]
# ## TODO 7 — `planejar()`, `interpretar_pedido()` e `narrar()`

# %%
def planejar(origem, destino, fechadas=(), estrategia="bfs"):
    """Planeja a viagem e devolve um dicionário com o resultado + diagnóstico."""
    fechadas = set(fechadas)
    kb = inferir(fatos_base(fechadas))

    busca = {"bfs": bfs_rota, "dfs": dfs_rota,
             "menos_baldeacoes": menos_baldeacoes_rota,
             "mais_rapida": rota_mais_rapida}[estrategia]
    caminho, visitadas = busca(origem, destino, fechadas)

    resultado = {
        "origem": origem,
        "destino": destino,
        "fechadas": sorted(fechadas),
        "estrategia": estrategia,
        "caminho": caminho,
        "visitadas": visitadas,
        "paradas": None if caminho is None else len(caminho) - 1,
        "baldeacoes": [] if caminho is None else marcar_baldeacoes(caminho),
        "cortadas": [f[1] for f in consultar(kb, "linha_cortada")],
        "integracoes": [f[1] for f in consultar(kb, "integracao")],
        "kb": kb,
    }
    if caminho is not None:
        resultado["tempo_min"] = resultado["paradas"] * 2 + len(resultado["baldeacoes"]) * 5
    return resultado


# ------------------------------------------------- interpretação de linguagem
def _norm(txt):
    txt = unicodedata.normalize("NFD", txt.lower())
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", txt).strip()


_INDICE = {_norm(e): e for e in ESTACOES}


def resolver_estacao(nome):
    """Casa um texto livre com o nome oficial da estação (tolera acento/typo)."""
    chave = _norm(nome)
    if chave in _INDICE:
        return _INDICE[chave]
    for k, v in _INDICE.items():
        if k.startswith(chave) or chave in k:
            return v
    perto = difflib.get_close_matches(chave, _INDICE, n=1, cutoff=0.6)
    return _INDICE[perto[0]] if perto else None


def interpretar_pedido(texto):
    """'quero ir de Sé até Jabaquara com Paraíso fechada' -> dict do pedido."""
    bruto = texto.strip()

    # 1) primeiro tira as cláusulas de interdição, senão elas poluem o destino
    fechadas = []
    #   ...com [a] [estação] <NOME> fechada/interditada/paralisada
    # o 'com|sem|e' é obrigatório: sem ele o grupo lazy engoliria a frase toda
    padrao_fechada = re.compile(
        r"\b(?:com|sem|e)\b\s+(?:a\s+)?(?:esta[cç][aã]o\s+)?"
        r"([A-Za-zÀ-ÿ0-9.'\-]+(?:\s+[A-Za-zÀ-ÿ0-9.'\-]+){0,3}?)\s+"
        r"(?:fechad[ao]|interditad[ao]|paralisad[ao]|em\s+obras)",
        re.IGNORECASE)
    for m in padrao_fechada.finditer(bruto):
        est = resolver_estacao(m.group(1))
        if est:
            fechadas.append(est)
    bruto = padrao_fechada.sub(" ", bruto)

    # 2) origem e destino
    m = re.search(r"\bde\s+(.+?)\s+(?:para|até|ate|rumo\s+a|a)\s+(.+?)\s*$",
                  bruto, re.IGNORECASE)
    if not m:
        m = re.search(r"^\s*(.+?)\s*(?:->|→|,)\s*(.+?)\s*$", bruto)
    if not m:
        return {"origem": None, "destino": None, "fechadas": fechadas,
                "erro": "não entendi a origem e o destino"}

    origem = resolver_estacao(m.group(1))
    destino = resolver_estacao(m.group(2))
    erro = None
    if origem is None:
        erro = f"estação de origem desconhecida: {m.group(1).strip()!r}"
    elif destino is None:
        erro = f"estação de destino desconhecida: {m.group(2).strip()!r}"
    return {"origem": origem, "destino": destino,
            "fechadas": sorted(set(fechadas)), "erro": erro}


# ----------------------------------------------------------------- narração
def narrar(res):
    """Transforma o resultado de planejar() em texto para humano."""
    linhas_txt = []
    if res["fechadas"]:
        linhas_txt.append("⚠️  Fechada(s): " + ", ".join(res["fechadas"]))

    if res["caminho"] is None:
        linhas_txt.append(
            f"❌ Sem rota de {res['origem']} para {res['destino']}.")
        for l in res["cortadas"]:
            linhas_txt.append(
                f"   Motivo (R7): a {NOMES_LINHA[l]} está cortada — a estação "
                f"fechada não é terminal, então parte a linha em dois trechos.")
        if not res["cortadas"]:
            linhas_txt.append("   Motivo: não há integração aberta entre as linhas.")
        linhas_txt.append(f"   Estações visitadas na busca: {len(res['visitadas'])}")
        return "\n".join(linhas_txt)

    caminho = res["caminho"]
    baldeacoes = res["baldeacoes"]
    troca_em = {b[0] for b in baldeacoes}

    linha_atual = caminho[1][1]
    inicio = caminho[0][0]
    linhas_txt.append(
        f"🚇 {res['origem']} → {res['destino']}: {res['paradas']} paradas, "
        f"{len(baldeacoes)} baldeação(ões), ~{res['tempo_min']} min.")
    linhas_txt.append("")

    trecho_ini = inicio
    for i in range(1, len(caminho)):
        est, linha = caminho[i]
        if linha != linha_atual or i == len(caminho) - 1:
            fim = est if linha == linha_atual else caminho[i - 1][0]
            n = _paradas_entre(caminho, trecho_ini, fim)
            linhas_txt.append(
                f"  • Pegue a {NOMES_LINHA[linha_atual]} em {trecho_ini} "
                f"e vá até {fim} ({n} parada(s)).")
            if fim in troca_em:
                nova = linha
                linhas_txt.append(
                    f"    ↳ Baldeação em {fim}: troque para a {NOMES_LINHA[nova]}.")
            trecho_ini = fim
            linha_atual = linha

    linhas_txt.append("")
    linhas_txt.append("  Itinerário: " + " → ".join(e for e, _ in caminho))
    linhas_txt.append(f"  (busca {res['estrategia'].upper()}, "
                      f"{len(res['visitadas'])} estações visitadas)")
    return "\n".join(linhas_txt)


def _paradas_entre(caminho, a, b):
    nomes = [e for e, _ in caminho]
    return abs(nomes.index(b) - nomes.index(a))

# %% [markdown]
# ## TODO 8 — mapa HTML com as cores oficiais

# %%
def mapa_html(res=None):
    """Desenha as 3 linhas; destaca rota, baldeações e estações fechadas."""
    fechadas = set(res["fechadas"]) if res else set()
    na_rota = {e for e, _ in res["caminho"]} if res and res["caminho"] else set()
    baldeacoes = {b[0] for b in res["baldeacoes"]} if res else set()
    integracoes = {e for e in ESTACOES
                   if sum(e in seq for seq in LINHAS.values()) > 1}

    out = ["<div style='font-family:system-ui,sans-serif;font-size:13px'>"]
    for linha, seq in LINHAS.items():
        cor = CORES[linha]
        out.append(
            f"<div style='margin:14px 0'>"
            f"<div style='font-weight:700;color:{cor};margin-bottom:6px'>"
            f"● {NOMES_LINHA[linha]}</div>"
            f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:2px'>")
        for i, est in enumerate(seq):
            if i:
                out.append(f"<span style='color:{cor};font-weight:700'>—</span>")

            fundo, texto, borda, extra = "#fff", "#333", cor, ""
            if est in fechadas:
                fundo, texto, borda = "#eee", "#999", "#bbb"
                extra = "text-decoration:line-through;"
            elif est in na_rota:
                fundo, texto = cor, "#fff"
                extra = "font-weight:700;"
            elif est in integracoes:
                extra = "font-weight:600;"

            anel = ("box-shadow:0 0 0 3px #FFC400;" if est in baldeacoes else "")
            marca = " ⇄" if est in baldeacoes else ("  ⛔" if est in fechadas else "")
            out.append(
                f"<span style='display:inline-block;padding:3px 8px;"
                f"border:2px solid {borda};border-radius:12px;background:{fundo};"
                f"color:{texto};{extra}{anel}'>{est}{marca}</span>")
        out.append("</div></div>")

    out.append(
        "<div style='margin-top:10px;color:#666'>"
        "⇄ baldeação &nbsp;•&nbsp; ⛔ estação fechada &nbsp;•&nbsp; "
        "negrito = estação de integração</div></div>")
    return "".join(out)


def mostrar(res):
    from IPython.display import HTML, display
    print(narrar(res))
    display(HTML(mapa_html(res)))

# %% [markdown]
# ## Bônus 1 e 2 — menos baldeações e rota mais rápida
#
# * **Menos baldeações**: o estado da busca vira `(estação, linha_atual)` e o
#   custo é o nº de trocas (Dijkstra com custo 0 por trecho e 1 por troca).
# * **Mais rápida**: 2 min por trecho, +5 min por baldeação.

# %%
def _dijkstra(origem, destino, fechadas, custo_trecho, custo_troca):
    fechadas = set(fechadas)
    visitadas = []
    if origem in fechadas or destino in fechadas:
        return None, visitadas

    inicio = (origem, None)
    dist = {inicio: 0}
    veio = {inicio: None}
    heap = [(0, origem, None)]
    vistos = set()

    while heap:
        d, est, linha = heapq.heappop(heap)
        if (est, linha) in vistos:
            continue
        vistos.add((est, linha))
        visitadas.append(est)
        if est == destino:
            # desenrola o caminho no espaço de estados (estação, linha)
            caminho, no = [], (est, linha)
            while no is not None:
                caminho.append((no[0], no[1]))
                no = veio[no]
            caminho.reverse()
            return caminho, visitadas
        for viz, nova in vizinhos(est, fechadas):
            extra = custo_trecho + (custo_troca if linha and nova != linha else 0)
            if dist.get((viz, nova), float("inf")) > d + extra:
                dist[(viz, nova)] = d + extra
                veio[(viz, nova)] = (est, linha)
                heapq.heappush(heap, (d + extra, viz, nova))
    return None, visitadas


def menos_baldeacoes_rota(origem, destino, fechadas=frozenset()):
    return _dijkstra(origem, destino, fechadas, custo_trecho=0, custo_troca=1)


def rota_mais_rapida(origem, destino, fechadas=frozenset()):
    return _dijkstra(origem, destino, fechadas, custo_trecho=2, custo_troca=5)

# %% [markdown]
# ## TODO 9 — painel interativo (ipywidgets)

# %%
def painel():
    import ipywidgets as w
    from IPython.display import HTML, display, clear_output

    origem = w.Dropdown(options=ESTACOES, value="Tucuruvi", description="Origem:")
    destino = w.Dropdown(options=ESTACOES, value="Corinthians-Itaquera",
                         description="Destino:")
    fechadas = w.SelectMultiple(options=ESTACOES, description="Fechadas:",
                                rows=8, layout=w.Layout(width="320px"))
    estrategia = w.RadioButtons(
        options=[("Menos paradas (BFS)", "bfs"),
                 ("Profundidade (DFS)", "dfs"),
                 ("Menos baldeações", "menos_baldeacoes"),
                 ("Mais rápida (Dijkstra)", "mais_rapida")],
        value="bfs", description="Busca:")
    pedido = w.Text(description="Pedido:", placeholder="de Sé até Jabaquara "
                                                       "com Paraíso fechada",
                    layout=w.Layout(width="520px"))
    ir = w.Button(description="Planejar viagem", button_style="primary")
    limpar = w.Button(description="Limpar fechadas")
    saida = w.Output()

    def _rodar(_=None):
        with saida:
            clear_output()
            if pedido.value.strip():
                p = interpretar_pedido(pedido.value)
                if p.get("erro"):
                    print("❌", p["erro"])
                    return
                origem.value, destino.value = p["origem"], p["destino"]
                if p["fechadas"]:
                    fechadas.value = tuple(p["fechadas"])
            res = planejar(origem.value, destino.value,
                           fechadas.value, estrategia.value)
            print(narrar(res))
            display(HTML(mapa_html(res)))

    ir.on_click(_rodar)
    limpar.on_click(lambda _: setattr(fechadas, "value", ()))
    display(w.VBox([
        w.HTML("<h3>🚇 Planejador de viagem — Metrô SP</h3>"),
        pedido,
        w.HBox([w.VBox([origem, destino, estrategia]), fechadas]),
        w.HBox([ir, limpar]),
        saida,
    ]))
    _rodar()

# %% [markdown]
# ## TODO 10 — bateria de testes
#
# 6 casos obrigatórios + 2 casos do grupo.

# %%
CASOS = [
    # (#, origem, destino, fechadas, paradas_esperadas, baldeações_esperadas)
    (1, "Tucuruvi", "Corinthians-Itaquera", [], 22, [{"Sé"}]),
    (2, "Vila Madalena", "Jabaquara", [], 14, [{"Paraíso", "Ana Rosa"}]),
    (3, "Palmeiras-Barra Funda", "Vila Prudente", [], 16,
     [{"Sé"}, {"Paraíso", "Ana Rosa"}]),
    (4, "Tucuruvi", "Brás", ["Sé"], None, None),
    (5, "Vila Madalena", "Jabaquara", ["Paraíso"], None, None),
    (6, "Vila Prudente", "Jabaquara", ["Paraíso"], 13, [{"Ana Rosa"}]),
    # --- casos do grupo ---
    (7, "Luz", "Tamanduateí", [], 12, [{"Paraíso", "Ana Rosa"}]),
    (8, "Palmeiras-Barra Funda", "Jabaquara", ["Sé"], None, None),
]


def rodar_testes(verboso=True):
    ok = 0
    for n, orig, dest, fech, paradas_esp, bald_esp in CASOS:
        res = planejar(orig, dest, fech)
        obtido_paradas = res["paradas"]
        obtidas_bald = [b[0] for b in res["baldeacoes"]]

        passou = obtido_paradas == paradas_esp
        if passou and bald_esp is not None:
            passou = (len(obtidas_bald) == len(bald_esp) and
                      all(e in esperado
                          for e, esperado in zip(obtidas_bald, bald_esp)))

        ok += passou
        marca = "✅" if passou else "❌"
        cen = ", ".join(fech) + " fechada" if fech else "normal"
        esp = "Sem rota" if paradas_esp is None else (
            f"{paradas_esp} paradas, {len(bald_esp)} baldeação(ões)")
        got = "Sem rota" if obtido_paradas is None else (
            f"{obtido_paradas} paradas, {len(obtidas_bald)} baldeação(ões)"
            + (f" ({', '.join(obtidas_bald)})" if obtidas_bald else ""))
        print(f"{marca} #{n} {orig} → {dest} [{cen}]")
        print(f"     esperado: {esp}")
        print(f"     obtido  : {got}")
        if verboso and res["caminho"]:
            _, vis_dfs = dfs_rota(orig, dest, set(fech))
            print(f"     esforço : BFS {len(res['visitadas'])} visitadas | "
                  f"DFS {len(vis_dfs)} visitadas")
        print()

    print(f"=== {ok}/{len(CASOS)} testes passaram ===")
    return ok == len(CASOS)


rodar_testes()

# %% [markdown]
# ## Demonstração

# %%
for texto in [
    "quero ir de Tucuruvi para Corinthians-Itaquera",
    "de vila madalena ate jabaquara com Paraíso fechada",
    "de Vila Prudente para Jabaquara com a estação Paraíso interditada",
]:
    p = interpretar_pedido(texto)
    print(f">>> {texto}")
    print(f"    entendido: {p}")
    if not p.get("erro"):
        print(narrar(planejar(p["origem"], p["destino"], p["fechadas"])))
    print("-" * 70)

# %%
# Comparação entre estratégias (bônus 1 e 2)
for estr in ["bfs", "menos_baldeacoes", "mais_rapida"]:
    r = planejar("Palmeiras-Barra Funda", "Vila Prudente", [], estr)
    print(f"{estr:>18}: {r['paradas']} paradas, "
          f"{len(r['baldeacoes'])} baldeação(ões), ~{r['tempo_min']} min")

# %%
# Painel interativo — rode em um Jupyter com ipywidgets instalado
painel()
