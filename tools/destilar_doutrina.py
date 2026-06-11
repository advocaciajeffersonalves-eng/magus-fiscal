"""
Destilação de doutrina jurídica — 100% LOCAL via Ollama (zero token de API).

Extrai o texto de um PDF de doutrina, divide em blocos, e usa um modelo local
(Ollama) para destilar cada bloco num checklist de boas práticas. Consolida tudo
num guia compacto salvo em templates/_doutrina/.

Uso: python tools/destilar_doutrina.py "<caminho do PDF>" [modelo] [pag_ini] [pag_fim]
  modelo padrão: qwen2.5:14b  (cai para llama3.2 se não houver)
"""
import os, sys, json, urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "templates", "_doutrina")
OLLAMA = "http://localhost:11434/api/generate"
PAGINAS_POR_BLOCO = 4


def ollama(modelo, prompt):
    body = json.dumps({"model": modelo, "prompt": prompt, "stream": False,
                       "options": {"temperature": 0.2}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["resposta" if False else "response"].strip()


def destilar(pdf_path, modelo, pag_ini, pag_fim):
    import pdfplumber
    os.makedirs(SAIDA, exist_ok=True)
    nome = os.path.splitext(os.path.basename(pdf_path))[0]
    partes = []
    with pdfplumber.open(pdf_path) as pdf:
        fim = min(pag_fim or len(pdf.pages), len(pdf.pages))
        blocos = list(range(pag_ini, fim, PAGINAS_POR_BLOCO))
        for n, ini in enumerate(blocos, 1):
            texto = "\n".join((pdf.pages[i].extract_text() or "")
                              for i in range(ini, min(ini + PAGINAS_POR_BLOCO, fim)))
            if len(texto.strip()) < 200:
                continue
            prompt = (
                "Você é um assistente jurídico. Leia o trecho de doutrina de Direito Civil "
                "abaixo e extraia, em português, as regras práticas e cuidados que um advogado "
                "deve observar ao redigir contratos. Responda em tópicos curtos e objetivos, "
                "citando os artigos de lei quando o texto citar. Não invente.\n\nTRECHO:\n" + texto
            )
            try:
                resumo = ollama(modelo, prompt)
            except Exception as e:
                resumo = f"[erro no bloco {n}: {e}]"
            partes.append(f"### Bloco {n} (pág. {ini+1}-{min(ini+PAGINAS_POR_BLOCO, fim)})\n{resumo}")
            print(f"  bloco {n}/{len(blocos)} destilado ({len(resumo)} chars)", flush=True)

    guia = f"# Guia de Boas Práticas — {nome}\n\n_Destilado localmente (Ollama/{modelo}) — zero token de API._\n\n" + "\n\n".join(partes)
    out = os.path.join(SAIDA, f"guia_{nome[:40].strip().replace(' ','_')}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(guia)
    print(f"\nGuia salvo em: {out}  ({len(guia):,} chars)")


if __name__ == "__main__":
    pdf = sys.argv[1]
    modelo = sys.argv[2] if len(sys.argv) > 2 else "qwen2.5:14b"
    pag_ini = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    pag_fim = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    destilar(pdf, modelo, pag_ini, pag_fim or None)
