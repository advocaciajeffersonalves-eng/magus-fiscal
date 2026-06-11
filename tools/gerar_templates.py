"""
Geração de rascunhos de template — 100% LOCAL via Ollama qwen2.5:14b (zero token de API).

Para cada contrato original do Drive (famílias ainda sem wizard curado), o modelo
local marca os dados variáveis como {{CAMPO}} e sugere módulos opcionais. Salva
template.md + wizard.json em templates/_gerados/<slug>/ (gitignored, rascunho até
curadoria). Dados sensíveis residuais são mascarados por segurança.

Uso: python tools/gerar_templates.py [limite]    (limite opcional p/ teste)
"""
import os, re, sys, json, urllib.request, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
from ingest_contratos import extrair_texto, mascarar  # reuso (zero IA)

DRIVE = os.path.expanduser(
    "~/Library/CloudStorage/GoogleDrive-advocaciajeffersonalves@gmail.com/"
    "Meu Drive/MAGUS - Contratos Modelo")
SAIDA = os.path.join(RAIZ, "templates", "_gerados")
OLLAMA = "http://localhost:11434/api/generate"
MODELO = "qwen2.5:14b"
JA_CURADAS = {"Compra e Venda de Imóveis", "Direito Agrário e Rural",
              "Permuta Imobiliária", "vesting", "Doutrinas"}

# linhas de "ruído" dos modelos gerados por IA (Napoleão.AI etc.)
RUIDO = re.compile(r"^(Resposta de Agente|Data:|📋|⚠️|🟡|🔴|📊|📋|⚡|\[Ferramentas|Napoleão|"
                   r"\*\*RESSALVA|\*\*ADVERT|\*\*Nota|Aqui está|Claro\.|Agora sim)", re.I)


def limpar(texto: str) -> str:
    linhas = [l for l in texto.splitlines() if not RUIDO.match(l.strip())]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50]


def ollama(prompt: str) -> str:
    body = json.dumps({"model": MODELO, "prompt": prompt, "stream": False,
                       "format": "json", "options": {"temperature": 0.1}}).encode()
    req = urllib.request.Request(OLLAMA, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["response"]


PROMPT = """Você é um assistente jurídico. Analise o contrato abaixo e responda APENAS com um JSON válido neste formato exato:
{{"titulo":"<Família · Tipo específico do contrato>",
  "campos":[{{"key":"NOME_MAIUSCULO","label":"rótulo amigável","trecho":"<texto EXATO do contrato a ser substituído por este campo>"}}],
  "escolhas":[{{"label":"pergunta","opcoes":[{{"label":"opção","modulo":"M_NOME"}}]}}],
  "toggles":[{{"key":"M_NOME","label":"cláusula opcional ligar/desligar"}}]}}
Regras: 'campos' são os dados que mudam por cliente (nomes, valores, prazos, datas, endereços, matrículas) — use o texto exato em 'trecho'. 'escolhas' e 'toggles' são cláusulas que variam conforme o caso. Não invente. Família = "{familia}".

CONTRATO:
{corpo}"""


def processar(caminho, familia, nome):
    corpo = limpar(extrair_texto(caminho))[:9000]
    if len(corpo) < 300:
        return {"familia": familia, "arquivo": nome, "erro": "corpo curto"}
    try:
        data = json.loads(ollama(PROMPT.format(familia=familia, corpo=corpo)))
    except Exception as e:
        return {"familia": familia, "arquivo": nome, "erro": f"json: {str(e)[:60]}"}

    # monta template.md substituindo os trechos por {{CAMPO}}
    template = corpo
    campos_ok = []
    for c in data.get("campos", []):
        key, trecho = c.get("key", ""), c.get("trecho", "")
        if key and trecho and trecho in template:
            template = template.replace(trecho, "{{" + key + "}}", 1)
            campos_ok.append({"key": key, "label": c.get("label", key)})
    template, _ = mascarar(template)  # segurança: mascara dados residuais não marcados

    wizard = {
        "titulo": data.get("titulo", f"{familia} · {nome[:30]}"),
        "grupos": [{"nome": "Dados do contrato", "campos": campos_ok}] if campos_ok else [],
        "escolhas": [e for e in data.get("escolhas", []) if e.get("opcoes")],
        "toggles": [t for t in data.get("toggles", []) if t.get("key")],
    }
    destino = os.path.join(SAIDA, slug(familia) + "__" + slug(os.path.splitext(nome)[0]))
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, "template.md"), "w", encoding="utf-8") as f:
        f.write("# " + wizard["titulo"] + "\n\n" + template + "\n")
    with open(os.path.join(destino, "wizard.json"), "w", encoding="utf-8") as f:
        json.dump(wizard, f, ensure_ascii=False, indent=2)
    return {"familia": familia, "arquivo": nome, "titulo": wizard["titulo"],
            "campos": len(campos_ok), "toggles": len(wizard["toggles"]), "destino": os.path.basename(destino)}


def main():
    limite = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    os.makedirs(SAIDA, exist_ok=True)
    alvos = []
    for raiz, dirs, arqs in os.walk(DRIVE):
        dirs[:] = [d for d in dirs if d not in JA_CURADAS and not d.startswith("_")]
        fam = os.path.relpath(raiz, DRIVE).split(os.sep)[0]
        if fam in JA_CURADAS or fam == ".":
            continue
        for n in sorted(arqs):
            if n.lower().endswith((".docx", ".pdf")):
                alvos.append((os.path.join(raiz, n), fam, n))
    if limite:
        alvos = alvos[:limite]
    print(f"Processando {len(alvos)} contratos com {MODELO} (local, zero token)...\n", flush=True)
    indice = []
    for i, (cam, fam, nome) in enumerate(alvos, 1):
        r = processar(cam, fam, nome)
        indice.append(r)
        msg = r.get("erro") and f"ERRO {r['erro']}" or f"{r['campos']}c {r['toggles']}m · {r['titulo'][:50]}"
        print(f"  [{i}/{len(alvos)}] {fam[:18]:18} | {msg}", flush=True)
    json.dump(indice, open(os.path.join(SAIDA, "_indice.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    ok = sum(1 for r in indice if "erro" not in r)
    print(f"\nConcluído: {ok}/{len(indice)} gerados. Rascunhos em templates/_gerados/")


if __name__ == "__main__":
    main()
