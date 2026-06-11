"""
Processa o Vade Mecum (EPUB) extraindo só as normas relevantes ao negócio
(civil, imobiliário, empresarial, tributário, consumidor, trabalho) e salvando
cada uma em templates/_doutrina/lei_vm_*.md para indexação no RAG local.
Exclui áreas fora do escopo (penal, eleitoral, etc.). Roda quando atualizar
o Vade Mecum (semestral). Zero token.

Uso: python tools/processar_vademecum.py "<caminho do .epub>"
"""
import os, re, sys, zipfile, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOUT = os.path.join(RAIZ, "templates", "_doutrina")

# títulos a EXCLUIR (fora do escopo do negócio)
EXCLUIR = ["penal", "contraven", "eleitoral", "crian", "adolescente",
           "igualdade racial", "juventude", "antidroga", "diretrizes e bases",
           "educa", "servidores", "maria da penha", "responsabilidade fiscal"]


def _slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def _titulo(raw):
    m = re.search(r"<(h1|h2|title)[^>]*>(.*?)</\1>", raw, re.I | re.S)
    return re.sub(r"<[^>]+>", "", m.group(2)).strip() if m else ""


def _texto(raw):
    t = re.sub(r"<[^>]+>", " ", raw)
    t = re.sub(r"&#160;|&[a-zA-Z#0-9]+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main(epub):
    os.makedirs(DOUT, exist_ok=True)
    z = zipfile.ZipFile(epub)
    htmls = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html"))]
    incl, excl = [], []
    for n in sorted(htmls):
        raw = z.read(n).decode("utf-8", "ignore")
        titulo = _titulo(raw)
        txt = _texto(raw)
        if len(txt) < 20000:           # pula sumário, capa, metadados
            continue
        low = titulo.lower()
        if any(e in low for e in EXCLUIR):
            excl.append(titulo[:50]); continue
        with open(os.path.join(DOUT, f"lei_vm_{_slug(titulo)}.md"), "w", encoding="utf-8") as f:
            f.write(f"# {titulo}\n\n{txt}")
        incl.append(f"{titulo[:50]} ({len(txt)//1000}k)")
    # remove o Código Civil avulso (redundante — o Vade Mecum já o traz)
    cc = os.path.join(DOUT, "lei_codigo_civil.md")
    if os.path.exists(cc) and any("civil" in i.lower() and "processo" not in i.lower() for i in incl):
        os.remove(cc); print("  (removido lei_codigo_civil.md avulso — VM já tem)")
    print(f"\nINCLUÍDAS ({len(incl)}):")
    for i in incl: print("  ✓", i)
    print(f"\nEXCLUÍDAS ({len(excl)}):")
    for e in excl: print("  ✗", e)


if __name__ == "__main__":
    main(sys.argv[1])
