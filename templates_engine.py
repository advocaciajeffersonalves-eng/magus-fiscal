"""
Motor de templates (template-first) do MAGUS Fiscal.

Cada tipo de contrato pode ter um modelo próprio em templates/<tipo>/template.md,
com campos {{CAMPO}} e blocos de módulo [[NOME]]...[[/NOME]] que ligam/desligam
conforme as respostas do usuário. Renderizar é determinístico (custo ZERO de IA);
a IA só entra depois, no acabamento, se desejado.
"""
import os
import re
import json

BASE = os.path.join(os.path.dirname(__file__), "templates")


def descobrir() -> dict:
    """
    Descobre dinamicamente os tipos com modelo no banco: qualquer pasta
    templates/<slug>/ (que não comece com '_') contendo template.md E wizard.json.
    Retorna {titulo_do_wizard: slug_da_pasta}. Assim, gerar novas famílias é só
    criar os 2 arquivos — a ferramenta detecta sozinha.
    """
    mapa = {}
    if not os.path.isdir(BASE):
        return mapa
    # famílias curadas (templates/<slug>/) e rascunhos gerados (templates/_gerados/<slug>/)
    candidatos = [(s, s) for s in sorted(os.listdir(BASE)) if not s.startswith("_")]
    ger = os.path.join(BASE, "_gerados")
    if os.path.isdir(ger):
        candidatos += [(s, os.path.join("_gerados", s)) for s in sorted(os.listdir(ger))]
    for _slug, rel in candidatos:
        p = os.path.join(BASE, rel)
        if not os.path.isdir(p):
            continue
        if os.path.exists(os.path.join(p, "template.md")) and os.path.exists(os.path.join(p, "wizard.json")):
            titulo = _slug
            try:
                titulo = json.load(open(os.path.join(p, "wizard.json"), encoding="utf-8")).get("titulo", _slug)
            except Exception:
                pass
            mapa.setdefault(titulo, rel)
    return mapa


def _chave(tipo: str) -> str:
    """Casa o rótulo do tipo (pode vir com emoji/prefixo) com um título descoberto."""
    t = (tipo or "").strip()
    titulos = descobrir()
    # match exato primeiro, depois por contenção (mais específico vence)
    for k in titulos:
        if k.lower() == t.lower():
            return k
    for k in sorted(titulos, key=len, reverse=True):
        if k.lower() in t.lower() or t.lower() in k.lower():
            return k
    return t


def _pasta(tipo: str) -> str | None:
    return descobrir().get(_chave(tipo))


def tem_template(tipo: str) -> bool:
    """Diz se o tipo selecionado tem modelo no banco."""
    p = _pasta(tipo)
    return bool(p) and os.path.exists(os.path.join(BASE, p, "template.md"))


def carregar_template(tipo: str) -> str:
    with open(os.path.join(BASE, _pasta(tipo), "template.md"), encoding="utf-8") as f:
        return f.read()


def carregar_perguntas(tipo: str) -> str:
    """Retorna o roteiro de perguntas (markdown) do tipo, ou string vazia."""
    p = _pasta(tipo)
    caminho = os.path.join(BASE, p, "perguntas.md") if p else ""
    if caminho and os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return f.read()
    return ""


def carregar_wizard(tipo: str) -> dict:
    """Carrega a definição do wizard (grupos de campos, escolhas e toggles) do tipo."""
    p = _pasta(tipo)
    caminho = os.path.join(BASE, p, "wizard.json") if p else ""
    if caminho and os.path.exists(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    return {}


def listar_campos(template_str: str) -> list[str]:
    """Lista os campos {{CAMPO}} presentes no template, na ordem de aparição, sem repetir."""
    vistos, ordem = set(), []
    for m in re.findall(r"\{\{(\w+)\}\}", template_str):
        if m not in vistos:
            vistos.add(m); ordem.append(m)
    return ordem


def listar_modulos(template_str: str) -> list[str]:
    """Lista os nomes de módulos [[NOME]]...[[/NOME]] do template, sem repetir."""
    vistos, ordem = set(), []
    for m in re.findall(r"\[\[(\w+)\]\]", template_str):
        if m not in vistos:
            vistos.add(m); ordem.append(m)
    return ordem


def renderizar(template_str: str, campos: dict, modulos_ativos) -> str:
    """
    Renderiza o template de forma determinística (sem IA):
      1) inclui/exclui cada bloco de módulo conforme `modulos_ativos`;
      2) substitui {{CAMPO}} pelos valores de `campos`. Campos sem valor viram
         um marcador visível [PREENCHER: CAMPO] para o usuário completar depois.
    """
    ativos = set(modulos_ativos or [])

    # 1) Módulos — processa todos os blocos [[NOME]]...[[/NOME]] (inclusive repetidos).
    def _bloco(match):
        nome, conteudo = match.group(1), match.group(2)
        return conteudo if nome in ativos else ""
    texto = re.sub(r"\[\[(\w+)\]\](.*?)\[\[/\1\]\]", _bloco, template_str, flags=re.DOTALL)

    # 2) Campos — substitui {{CAMPO}} pelo valor; vazio vira marcador a completar.
    def _campo(match):
        nome = match.group(1)
        val = campos.get(nome) if campos else None
        val = (str(val).strip() if val is not None else "")
        return val if val else f"[PREENCHER: {nome}]"
    texto = re.sub(r"\{\{(\w+)\}\}", _campo, texto)

    # limpa linhas em branco em excesso deixadas por módulos removidos
    texto = re.sub(r"\n{3,}", "\n\n", texto).strip() + "\n"
    return texto
