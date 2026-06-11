"""
Pipeline de ingestão de contratos — LEITURA E ORGANIZAÇÃO sem IA (custo zero de token).

Lê os contratos do Drive, extrai o texto, MASCARA dados sigilosos (CPF, CNPJ, CEP,
valores, datas) trocando-os por campos {{...}}, conta a estrutura e salva um
rascunho de template por arquivo em templates/_rascunhos/<familia>/.
Imprime apenas um índice resumido (não despeja o conteúdo).

Uso: python tools/ingest_contratos.py
"""
import os, re, sys, json

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVE = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-advocaciajeffersonalves@gmail.com/"
    "Meu Drive/MAGUS - Contratos Modelo"
)
SAIDA = os.path.join(RAIZ, "templates", "_rascunhos")
IGNORAR_PASTAS = {"Doutrinas", "_originais", "_rascunhos"}  # doutrina é tratada à parte

# ── Máscaras de dados sigilosos/variáveis (determinístico) ───────────────────
MASCARAS = [
    (re.compile(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}"),          "{{CNPJ}}"),
    (re.compile(r"\d{3}\.\d{3}\.\d{3}-\d{2}"),                "{{CPF}}"),
    (re.compile(r"\b\d{5}-\d{3}\b"),                          "{{CEP}}"),
    (re.compile(r"R\$\s?[\d.]+(?:,\d{2})?"),                  "{{VALOR}}"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"),              "{{DATA}}"),
    (re.compile(r"\b\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}\b", re.I), "{{DATA}}"),
    (re.compile(r"\bNIRE\s*[:n.º]*\s*[\d.\-/]+", re.I),       "NIRE {{NIRE}}"),
]


def extrair_texto(caminho):
    if caminho.lower().endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(caminho).paragraphs)
    if caminho.lower().endswith(".pdf"):
        import pdfplumber
        with pdfplumber.open(caminho) as pdf:
            return "\n".join(pg.extract_text() or "" for pg in pdf.pages)
    return ""


def mascarar(texto):
    n = 0
    for rx, sub in MASCARAS:
        texto, c = rx.subn(sub, texto)
        n += c
    return texto, n


def estrutura(texto):
    linhas = [l.strip() for l in texto.splitlines() if l.strip()]
    titulo = linhas[0] if linhas else "(sem título)"
    clausulas = [l for l in linhas if re.match(r"^(CL[ÁA]USULA|\d+[\.ª]|[IVX]+\s*[-–])", l, re.I)]
    return titulo, len(linhas), len(clausulas)


def main():
    if not os.path.isdir(DRIVE):
        print("ERRO: pasta do Drive não encontrada."); sys.exit(1)
    indice = []
    for raiz, dirs, arquivos in os.walk(DRIVE):
        dirs[:] = [d for d in dirs if d not in IGNORAR_PASTAS]
        rel = os.path.relpath(raiz, DRIVE)
        if rel == ".":
            continue
        familia = rel.split(os.sep)[0]
        if familia in IGNORAR_PASTAS:
            continue
        destino = os.path.join(SAIDA, rel)
        for nome in sorted(arquivos):
            if not nome.lower().endswith((".docx", ".pdf")):
                continue
            try:
                texto = extrair_texto(os.path.join(raiz, nome))
            except Exception as e:
                indice.append({"familia": familia, "sub": rel, "arquivo": nome, "erro": str(e)[:80]})
                continue
            mascarado, n_masc = mascarar(texto)
            titulo, n_linhas, n_clau = estrutura(texto)
            os.makedirs(destino, exist_ok=True)
            base = os.path.splitext(nome)[0]
            with open(os.path.join(destino, base + ".md"), "w", encoding="utf-8") as f:
                f.write(mascarado)
            indice.append({"familia": familia, "sub": rel, "arquivo": nome, "titulo": titulo[:70],
                           "linhas": n_linhas, "clausulas": n_clau, "dados_mascarados": n_masc})
    # índice resumido
    with open(os.path.join(SAIDA, "_indice.json"), "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False, indent=2)
    print(f"Processados {len(indice)} arquivos. Rascunhos em templates/_rascunhos/\n")
    fam_atual = None
    for it in indice:
        if it["familia"] != fam_atual:
            fam_atual = it["familia"]; print(f"── {fam_atual} ──")
        if "erro" in it:
            print(f"   ⚠ {it['arquivo'][:50]} — ERRO: {it['erro']}")
        else:
            print(f"   {it['clausulas']:2}cl {it['dados_mascarados']:3}🔒  {it['titulo']}")


if __name__ == "__main__":
    main()
