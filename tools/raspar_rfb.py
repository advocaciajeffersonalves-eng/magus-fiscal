"""
Raspagem da legislação fiscal da RFB (SIJUT2) — navegador-robô (Playwright).
ZERO token de IA: o conteúdo é capturado por seletores, sem LLM.

Para cada tema: busca no SIJUT2, coleta os idAto dos resultados, captura o texto
de cada norma (renderizado por JS) e salva em templates/_doutrina/lei_rfb_<id>.md.
Ao final, indexa INCREMENTALMENTE no RAG (sem re-gerar o acervo). Cadência
respeitosa (pausa entre capturas). Pula normas já capturadas.

Uso: python tools/raspar_rfb.py "<tema1>" "<tema2>" ... [--max N]
"""
import os, re, sys, time
from playwright.sync_api import sync_playwright

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)  # permite importar rag_local rodando de tools/
DOUT = os.path.join(RAIZ, "templates", "_doutrina")
BASE = "http://normas.receita.fazenda.gov.br/sijut2consulta"
PAUSA = 1.5  # segundos entre capturas (cadência respeitosa)


def descobrir(pg, termo, max_ids):
    pg.goto(f"{BASE}/consulta.action", wait_until="networkidle", timeout=60000)
    pg.fill("#termoBusca", termo)
    pg.click("text=Buscar")
    pg.wait_for_load_state("networkidle", timeout=60000)
    time.sleep(2)
    ids = sorted(set(re.findall(r"idAto=(\d+)", pg.content())), key=int)
    return ids[:max_ids]


def capturar(pg, id_ato):
    pg.goto(f"{BASE}/link.action?idAto={id_ato}&visao=original",
            wait_until="networkidle", timeout=60000)
    time.sleep(1)
    titulo = pg.title().strip()
    texto = re.sub(r"\s+", " ", pg.inner_text("body")).strip()
    return titulo, texto


def raspar(temas, max_por_tema=10):
    os.makedirs(DOUT, exist_ok=True)
    novos, vistos = [], set()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        for termo in temas:
            try:
                ids = descobrir(pg, termo, max_por_tema)
            except Exception as e:
                print(f"  ✗ busca '{termo}': {str(e)[:50]}"); continue
            print(f"── tema '{termo}': {len(ids)} normas")
            for id_ato in ids:
                if id_ato in vistos:
                    continue
                vistos.add(id_ato)
                arq = os.path.join(DOUT, f"lei_rfb_{id_ato}.md")
                if os.path.exists(arq):
                    continue
                try:
                    titulo, texto = capturar(pg, id_ato)
                    if len(texto) > 1000:
                        with open(arq, "w", encoding="utf-8") as f:
                            f.write(f"# {titulo}\n\n{texto}")
                        novos.append(arq)
                        print(f"   ✓ {id_ato} {titulo[:55]} ({len(texto):,} chars)")
                    else:
                        print(f"   · {id_ato} (texto curto, pulado)")
                except Exception as e:
                    print(f"   ✗ {id_ato}: {str(e)[:40]}")
                time.sleep(PAUSA)
        b.close()
    if novos:
        import rag_local
        n = rag_local.adicionar(novos)
        print(f"\n{len(novos)} normas raspadas · {n} trechos indexados (incremental, zero token)")
    else:
        print("\nNenhuma norma nova capturada.")
    return novos


if __name__ == "__main__":
    args, mx, argv, i = [], 10, sys.argv[1:], 0
    while i < len(argv):
        if argv[i] == "--max":
            mx = int(argv[i + 1]); i += 2
        else:
            args.append(argv[i]); i += 1
    if not args:
        args = ["residência fiscal saída do país"]
    raspar(args, mx)
