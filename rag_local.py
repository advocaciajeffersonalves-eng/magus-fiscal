"""
Busca semântica LOCAL no acervo (RAG) — zero token de API.

Backend numpy: os embeddings ficam numa matriz binária (.npy, compacta e rápida)
e os textos num JSON paralelo. A busca é vetorizada (produto de matriz) — escala
para centenas de milhares de trechos. Suporta indexação INCREMENTAL (adicionar
novas normas sem re-gerar tudo). Embeddings via nomic-embed-text (Ollama local).
"""
import os, re, json, glob, urllib.request
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "templates")
DOUT = os.path.join(BASE, "_doutrina")
EMB_NPY = os.path.join(DOUT, "rag_embeddings.npy")
TEXTOS = os.path.join(DOUT, "rag_textos.json")
INDICE_JSON_LEGADO = os.path.join(DOUT, "indice_rag.json")
OLLAMA_EMB = "http://localhost:11434/api/embeddings"
MODELO_EMB = "nomic-embed-text"


def _embed(texto: str):
    body = json.dumps({"model": MODELO_EMB, "prompt": texto[:2000]}).encode()
    req = urllib.request.Request(OLLAMA_EMB, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["embedding"]


def _norm(v):
    v = np.asarray(v, dtype=np.float32)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-8)


def _chunks(texto: str, alvo: int = 700):
    """Fatia o texto em blocos de ~alvo caracteres. Funciona com leis (sem
    parágrafos): quebra por 'Art.' e por tamanho."""
    bruto = re.split(r"\n\s*\n", texto)
    pedacos = []
    for p in bruto:
        p = p.strip()
        if not p:
            continue
        partes = re.split(r"(?=Art\.\s*\d)", p) if "Art." in p else [p]
        for parte in partes:
            parte = parte.strip()
            while len(parte) > alvo * 2:
                corte = parte.rfind(" ", alvo, alvo * 2)
                corte = corte if corte != -1 else alvo * 2
                pedacos.append(parte[:corte].strip())
                parte = parte[corte:].strip()
            if parte:
                pedacos.append(parte)
    blocos, atual = [], ""
    for p in pedacos:
        if len(atual) + len(p) > alvo and atual:
            blocos.append(atual); atual = p
        else:
            atual = (atual + "\n" + p).strip()
    if atual:
        blocos.append(atual)
    return [b for b in blocos if len(b) > 80]


_cache_emb = None
_cache_txt = None


def _carregar():
    global _cache_emb, _cache_txt
    if _cache_emb is None and os.path.exists(EMB_NPY) and os.path.exists(TEXTOS):
        _cache_emb = np.load(EMB_NPY)
        _cache_txt = json.load(open(TEXTOS, encoding="utf-8"))
    return _cache_emb, _cache_txt


def _salvar(matriz, textos):
    global _cache_emb, _cache_txt
    os.makedirs(DOUT, exist_ok=True)
    np.save(EMB_NPY, matriz)
    json.dump(textos, open(TEXTOS, "w", encoding="utf-8"), ensure_ascii=False)
    _cache_emb, _cache_txt = matriz, textos


def _fontes_md():
    return glob.glob(os.path.join(DOUT, "guia_*.md")) + glob.glob(os.path.join(DOUT, "lei_*.md"))


def indexar() -> int:
    """(Re)gera o índice inteiro a partir dos .md do acervo. Embeda tudo."""
    textos, embs = [], []
    for g in _fontes_md():
        conteudo = open(g, encoding="utf-8").read()
        fonte = os.path.basename(g)
        for ch in _chunks(conteudo):
            try:
                embs.append(_embed(ch)); textos.append({"texto": ch, "fonte": fonte})
            except Exception:
                pass
    _salvar(_norm(np.array(embs, dtype=np.float32)), textos)
    return len(textos)


def adicionar(caminhos_md: list) -> int:
    """Indexação INCREMENTAL: embeda só os arquivos novos e anexa ao índice
    existente, sem re-gerar tudo. Retorna quantos trechos foram adicionados."""
    emb, txt = _carregar()
    novos_t, novos_e = [], []
    for g in caminhos_md:
        if not os.path.exists(g):
            continue
        fonte = os.path.basename(g)
        for ch in _chunks(open(g, encoding="utf-8").read()):
            try:
                novos_e.append(_embed(ch)); novos_t.append({"texto": ch, "fonte": fonte})
            except Exception:
                pass
    if not novos_t:
        return 0
    nova_matriz = _norm(np.array(novos_e, dtype=np.float32))
    if emb is not None and len(emb):
        nova_matriz = np.vstack([emb, nova_matriz])
        txt = (txt or []) + novos_t
    else:
        txt = novos_t
    _salvar(nova_matriz, txt)
    return len(novos_t)


def buscar(consulta: str, k: int = 4) -> list:
    """Retorna os k trechos mais relevantes. Busca vetorizada (numpy). [] se vazio."""
    emb, txt = _carregar()
    if emb is None or not len(emb):
        return []
    try:
        q = _norm(_embed(consulta))
    except Exception:
        return []
    scores = emb @ q
    k = min(k, len(scores))
    idx = np.argpartition(-scores, k - 1)[:k]
    idx = idx[np.argsort(-scores[idx])]
    return [txt[i]["texto"] for i in idx]


def contexto(consulta: str, k: int = 4) -> str:
    """Trechos relevantes formatados para injetar no prompt (vazio se nada)."""
    trechos = buscar(consulta, k)
    if not trechos:
        return ""
    return ("\n\nEMBASAMENTO (doutrina/legislação — use se pertinente, sem citar que veio daqui):\n"
            + "\n---\n".join(trechos))


def migrar_do_json() -> int:
    """Converte o índice legado (indice_rag.json) para o backend numpy SEM
    re-embedar — reaproveita os embeddings já calculados."""
    if not os.path.exists(INDICE_JSON_LEGADO):
        return 0
    idx = json.load(open(INDICE_JSON_LEGADO, encoding="utf-8"))
    matriz = _norm(np.array([it["emb"] for it in idx], dtype=np.float32))
    textos = [{"texto": it["texto"], "fonte": it.get("fonte", "")} for it in idx]
    _salvar(matriz, textos)
    return len(idx)


if __name__ == "__main__":
    print("Indexando acervo (local, zero token)...")
    print(f"Índice criado com {indexar()} trechos.")
