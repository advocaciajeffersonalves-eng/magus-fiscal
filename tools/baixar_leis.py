"""
Baixa as leis-chave do site oficial (Planalto) e salva como texto em
templates/_doutrina/lei_*.md, para serem indexadas no RAG local (Fase C).
Roda uma vez (e quando quiser atualizar). Requer acesso à rede.

Uso: python tools/baixar_leis.py
"""
import os, re, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOUT = os.path.join(RAIZ, "templates", "_doutrina")

P = "https://www.planalto.gov.br/ccivil_03"
LEIS = {
    "codigo_civil":        ("Código Civil (Lei 10.406/2002)",            f"{P}/leis/2002/l10406compilada.htm"),
    "registros_publicos":  ("Lei de Registros Públicos (6.015/1973)",    f"{P}/leis/l6015compilada.htm"),
    "inquilinato":         ("Lei do Inquilinato (8.245/1991)",           f"{P}/leis/l8245.htm"),
    "estatuto_terra":      ("Estatuto da Terra (4.504/1964)",            f"{P}/leis/l4504.htm"),
    "incorporacoes":       ("Lei de Incorporações (4.591/1964)",         f"{P}/leis/l4591.htm"),
    "parcelamento_solo":   ("Parcelamento do Solo Urbano (6.766/1979)",  f"{P}/leis/l6766.htm"),
    "alienacao_fiduciaria":("Alienação Fiduciária de Imóvel (9.514/1997)",f"{P}/leis/l9514.htm"),
    "arbitragem":          ("Lei de Arbitragem (9.307/1996)",            f"{P}/leis/l9307.htm"),
    "lgpd":                ("LGPD (13.709/2018)",                        f"{P}/_ato2015-2018/2018/lei/l13709.htm"),
}


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("latin-1", errors="ignore")


def extrair(html):
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"&nbsp;|&[a-zA-Z]+;", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def main():
    os.makedirs(DOUT, exist_ok=True)
    for slug, (nome, url) in LEIS.items():
        try:
            txt = extrair(baixar(url))
            if len(txt) < 1000:
                print(f"  ⚠ {nome}: conteúdo curto, pulando"); continue
            with open(os.path.join(DOUT, f"lei_{slug}.md"), "w", encoding="utf-8") as f:
                f.write(f"# {nome}\n\n{txt}")
            print(f"  ✓ {nome}: {len(txt):,} chars")
        except Exception as e:
            print(f"  ✗ {nome}: {str(e)[:60]}")


if __name__ == "__main__":
    main()
