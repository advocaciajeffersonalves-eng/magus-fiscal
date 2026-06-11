"""
Processa o acervo de Súmulas e Acórdãos do CARF (PDFs/DOCX) — zero token.
Extrai o texto, FILTRA arquivos administrativos (questionário, currículo, vagas...),
DEDUPLICA cópias "(1)(2)", salva em templates/_doutrina/lei_carf_<slug>.md e indexa
INCREMENTAL no RAG. Jurisprudência é pública — não mascara.

Uso: python tools/processar_carf.py
"""
import os, re, sys, glob, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
DOUT = os.path.join(RAIZ, "templates", "_doutrina")
PASTA = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-advocaciajeffersonalves@gmail.com/"
    "Meu Drive/MAGUS - Contratos Modelo/SUMULA E ACORDÃO DO CARF")

# nomes que NÃO são jurisprudência (administrativos do CARF) → excluir
LIXO = ["questionario", "curriculo", "vaga", "mandato", "satisfacao", "quadro",
        "declaracoes", "tabela-ex", "modelo-de", "conselheiros-fazendarios",
        "mini-curriculo", "dados-abertos-gerenciais", "ata de julgamento"]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50]


def nome_base(nome):
    # remove sufixo de cópia " (1)", " (2)" e extensão p/ dedup
    n = re.sub(r"\s*\(\d+\)\s*$", "", os.path.splitext(nome)[0])
    return n.strip()


def extrai(p):
    if p.lower().endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(p) as pdf:
            return "\n".join(pg.extract_text() or "" for pg in pdf.pages)
    if p.lower().endswith(".docx"):
        from docx import Document
        return "\n".join(x.text for x in Document(p).paragraphs)
    return ""


def main():
    arqs = glob.glob(os.path.join(PASTA, "*.pdf")) + glob.glob(os.path.join(PASTA, "*.docx"))
    vistos, novos, pulados = set(), [], {"lixo": 0, "dup": 0, "curto": 0, "erro": 0}
    print(f"Encontrados {len(arqs)} arquivos. Processando (zero token)...", flush=True)
    for p in sorted(arqs):
        nome = os.path.basename(p)
        low = nome.lower()
        if any(x in low for x in LIXO):
            pulados["lixo"] += 1; continue
        base = nome_base(nome)
        if base in vistos:
            pulados["dup"] += 1; continue
        vistos.add(base)
        destino = os.path.join(DOUT, f"lei_carf_{slug(base)}.md")
        if os.path.exists(destino):
            continue
        try:
            txt = re.sub(r"\s+", " ", extrai(p)).strip()
        except Exception:
            pulados["erro"] += 1; continue
        if len(txt) < 800:
            pulados["curto"] += 1; continue
        with open(destino, "w", encoding="utf-8") as f:
            f.write(f"# CARF — {base}\n\n{txt}")
        novos.append(destino)
        if len(novos) % 20 == 0:
            print(f"  {len(novos)} processados...", flush=True)
    print(f"\nProcessados: {len(novos)} | pulados: {pulados}", flush=True)
    if novos:
        import rag_local
        print("Indexando incremental (embeddings locais, zero token)...", flush=True)
        n = rag_local.adicionar(novos)
        print(f"{len(novos)} peças do CARF · {n} trechos indexados.", flush=True)
    print("PROCESSAMENTO_CARF_FINALIZADO", flush=True)


if __name__ == "__main__":
    main()
