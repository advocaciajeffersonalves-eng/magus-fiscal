"""
Motor de Diagnóstico de Residência Fiscal Brasil–EUA — MAGUS Fiscal.

LÓGICA PURA (zero token de IA, custo zero por uso). Recebe as respostas do
wizard e devolve: classificação, pontuação de risco (0-100), alertas, providências,
documentos a reunir, perguntas para a reunião e as fontes legais.

⚠️ AS REGRAS ABAIXO SÃO PRELIMINARES E DEVEM SER VALIDADAS POR ADVOGADO
TRIBUTARISTA. Estão em estruturas parametrizáveis para edição sem reescrever código.
Base: IN SRF 208/2002 (residência fiscal/saída), Lei 14.754/2023 (offshores),
Perguntão IRPF, IN RFB 2.180/2024, SC Cosit 56.
"""

VERSAO_MOTOR = "1.0-preliminar"

# ─── Fontes legais (citadas no relatório) ────────────────────────────────────
FONTES_LEGAIS = {
    "residencia": "IN SRF nº 208/2002 — regras de residência fiscal, saída definitiva e tributação de não residentes.",
    "csdp_dsdp": "Comunicação e Declaração de Saída Definitiva do País — Perguntas e Respostas IRPF (Receita Federal).",
    "carne_leao": "Carnê-leão sobre rendimentos de fonte no exterior recebidos enquanto residente fiscal no Brasil (IN SRF 208/2002; Perguntão IRPF).",
    "offshores": "Lei nº 14.754/2023 (Lei das Offshores) e IN RFB nº 2.180/2024 — tributação de entidades controladas no exterior.",
    "llc": "Solução de Consulta Cosit nº 56 — tratamento de LLC norte-americana para residente fiscal brasileiro.",
    "sem_tratado": "Inexistência de tratado amplo Brasil–EUA contra dupla tributação; compensação limitada e condicionada (regras da RFB).",
    "mei_simples": "Restrições a MEI e Simples Nacional para não residentes (Perguntão IRPF; legislação do Simples).",
    "fonte_brasil": "Rendimentos de fonte brasileira de não residentes — tributação exclusiva na fonte (IN SRF 208/2002).",
    "cbe": "Declaração de Capitais Brasileiros no Exterior (CBE/DCBE) ao Banco Central, quando ativos no exterior atingem o limite legal.",
}


def _b(d, k):
    """Lê um campo booleano com tolerância (sim/True/1)."""
    v = d.get(k)
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("sim", "true", "1", "x")


def _meses_fora(d):
    try:
        return int(d.get("saiu_meses") or 0)
    except (ValueError, TypeError):
        return 0


# ─── Regras de ALERTA (condição → alerta + fonte) ────────────────────────────
# Cada regra: (id, função(respostas)->bool, texto, peso_no_score, chave_fonte)
REGRAS_ALERTA = [
    ("saida_fiscal_pendente",
     lambda d: d.get("carater_saida") == "definitivo" and not _b(d, "fez_csdp"),
     "Possível obrigação de Comunicação de Saída Definitiva (CSDP) não cumprida.", 12, "csdp_dsdp"),
    ("dsdp_atraso",
     lambda d: _meses_fora(d) >= 12 and not _b(d, "fez_dsdp"),
     "Declaração de Saída Definitiva (DSDP) possivelmente em atraso.", 12, "csdp_dsdp"),
    ("irpf_residente_inconsistente",
     lambda d: _meses_fora(d) >= 12 and _b(d, "continua_irpf_residente"),
     "Inconsistência: continua entregando IRPF como residente após viver nos EUA.", 18, "residencia"),
    ("carne_leao_exterior",
     lambda d: _meses_fora(d) < 12 and _b(d, "tem_renda_eua"),
     "Possível carnê-leão sobre renda do exterior no período ainda como residente fiscal brasileiro.", 10, "carne_leao"),
    ("compensacao_limitada",
     lambda d: _b(d, "pagou_imposto_eua") and _b(d, "tem_renda_eua"),
     "Imposto pago nos EUA tem compensação limitada no Brasil (não há tratado amplo Brasil–EUA).", 4, "sem_tratado"),
    ("offshore_14754",
     lambda d: _b(d, "tem_entidade_exterior") and (_meses_fora(d) < 12 or _b(d, "continua_irpf_residente")),
     "Entidade no exterior (LLC/holding/trust) controlada por possível residente fiscal — analisar Lei 14.754/2023.", 16, "offshores"),
    ("llc_classificacao",
     lambda d: _b(d, "tem_llc"),
     "A classificação da LLC para o IRS (EUA) não define automaticamente o tratamento fiscal brasileiro (SC Cosit 56).", 6, "llc"),
    ("mei_incompativel",
     lambda d: _b(d, "tem_mei") and (_meses_fora(d) >= 12 or _b(d, "fez_csdp")),
     "MEI possivelmente incompatível com a condição de não residente.", 10, "mei_simples"),
    ("simples_socio_nao_residente",
     lambda d: _b(d, "socio_simples") and (_meses_fora(d) >= 12 or _b(d, "fez_csdp")),
     "Sócio/administrador de empresa no Simples Nacional na condição de não residente — verificar restrições.", 8, "mei_simples"),
    ("fonte_brasil_nao_ajustada",
     lambda d: _b(d, "renda_brasil") and (_meses_fora(d) >= 12 or _b(d, "fez_csdp")) and not _b(d, "informou_fontes_pagadoras"),
     "Rendimentos de fonte brasileira sem ajuste à condição de não residente (tributação na fonte).", 8, "fonte_brasil"),
    ("cbe_obrigatorio",
     lambda d: _b(d, "ativos_acima_1mi"),
     "Ativos no exterior podem ultrapassar o limite da CBE/DCBE perante o Banco Central.", 6, "cbe"),
    ("documentacao_insuficiente",
     lambda d: not _b(d, "tem_tax_return") and _b(d, "tem_renda_eua"),
     "Documentação fiscal americana (tax returns) possivelmente insuficiente.", 5, "residencia"),
]


def _alertas(d):
    return [{"id": rid, "texto": txt, "peso": peso, "fonte": FONTES_LEGAIS[fk]}
            for rid, cond, txt, peso, fk in REGRAS_ALERTA if cond(d)]


# ─── CLASSIFICAÇÃO (6 categorias) ────────────────────────────────────────────
def _classificar(d):
    meses = _meses_fora(d)
    csdp, dsdp = _b(d, "fez_csdp"), _b(d, "fez_dsdp")
    irpf_res = _b(d, "continua_irpf_residente")
    vinculos = _b(d, "residencia_disponivel_brasil") or _b(d, "dependentes_brasil")
    definitivo = d.get("carater_saida") == "definitivo"

    # dados essenciais ausentes
    if not d.get("saiu_meses") and not d.get("carater_saida"):
        return ("inconclusivo", "Caso inconclusivo — faltam dados essenciais para o diagnóstico.")

    # contraditório / alto risco documental
    if meses >= 12 and irpf_res and (_b(d, "tem_mei") or _b(d, "socio_simples") or _b(d, "tem_renda_eua")):
        return ("alto_risco", "Caso contraditório ou de alto risco documental — vive nos EUA mas mantém condição/obrigações de residente no Brasil.")

    # transição (dentro dos 12 meses)
    if meses < 12 and not (csdp and dsdp):
        return ("transicao", "Caso em transição — dentro dos primeiros 12 meses de ausência; ainda residente fiscal brasileiro até regularização/decurso do prazo.")

    # não residente regular
    if definitivo and csdp and dsdp and not irpf_res:
        return ("nao_residente_regular", "Provavelmente não residente fiscal brasileiro com documentação regular.")

    # não residente com pendência documental
    if meses >= 12 and not (csdp and dsdp):
        return ("nao_residente_pendente", "Provavelmente não residente fiscal brasileiro, porém com documentação de saída pendente.")

    # ainda residente
    if irpf_res or vinculos or (meses < 12):
        return ("residente", "Provavelmente ainda residente fiscal brasileiro — sujeito à tributação da renda mundial.")

    return ("inconclusivo", "Caso inconclusivo — recomenda-se análise profissional detalhada.")


# ─── PONTUAÇÃO de risco (0-100) ──────────────────────────────────────────────
def _score(d, alertas):
    base = sum(a["peso"] for a in alertas)
    # agravantes adicionais
    if _b(d, "tem_entidade_exterior") and _b(d, "entidade_acumula_lucros"):
        base += 6
    if _b(d, "ativos_acima_1mi"):
        base += 4
    return max(0, min(100, base))


def _faixa(score):
    if score <= 25:  return ("baixo", "Risco baixo")
    if score <= 50:  return ("moderado", "Risco moderado")
    if score <= 75:  return ("alto", "Risco alto")
    return ("critico", "Risco crítico")


# ─── PROVIDÊNCIAS e DOCUMENTOS por situação ──────────────────────────────────
def _providencias(d, classif):
    p = []
    if not _b(d, "fez_csdp"):
        p.append("Avaliar a Comunicação de Saída Definitiva do País (CSDP).")
    if _meses_fora(d) >= 12 and not _b(d, "fez_dsdp"):
        p.append("Regularizar a Declaração de Saída Definitiva (DSDP) em atraso.")
    if _b(d, "continua_irpf_residente") and _meses_fora(d) >= 12:
        p.append("Revisar as últimas DIRPF entregues como residente e avaliar retificação.")
    if _meses_fora(d) < 12 and _b(d, "tem_renda_eua"):
        p.append("Apurar carnê-leão sobre rendimentos do exterior no período como residente.")
    if _b(d, "tem_mei"):
        p.append("Verificar a manutenção do MEI diante da condição de não residente.")
    if _b(d, "socio_simples"):
        p.append("Revisar participação/administração em empresa do Simples Nacional.")
    if _b(d, "tem_entidade_exterior"):
        p.append("Analisar a entidade no exterior sob a Lei 14.754/2023 (controle, renda passiva, lucros).")
    if _b(d, "ativos_acima_1mi"):
        p.append("Verificar obrigação de CBE/DCBE perante o Banco Central.")
    p.append("Atualizar cadastro (CPF, bancos, corretoras) conforme a condição fiscal correta.")
    return p


DOCUMENTOS = [
    "Comprovante de data de saída do Brasil (passaporte/visto).",
    "CSDP e DSDP, se apresentadas.",
    "Últimas DIRPF entregues no Brasil.",
    "Tax returns americanas dos últimos anos (1040, schedules).",
    "Documentos da(s) entidade(s) nos EUA (LLC/C-Corp: articles, EIN, K-1).",
    "Extratos de contas e investimentos no Brasil e no exterior.",
    "Comprovantes de imposto pago nos EUA.",
]

PERGUNTAS_REUNIAO = [
    "Qual foi a real intenção na data da saída — permanente ou temporária?",
    "Há documentação que comprove o vínculo de residência nos EUA (lease, contas, tax return)?",
    "A entidade americana tem renda ativa (operacional) ou passiva (investimentos)?",
    "Há lucros acumulados não distribuídos na entidade no exterior?",
    "Existem rendimentos de fonte brasileira ainda sendo recebidos?",
    "Quais declarações brasileiras foram entregues após a saída e em que condição?",
]


def montar_relatorio(form: dict, diag: dict) -> str:
    """Monta o texto (markdown) do relatório de diagnóstico nas 13 seções, a
    partir dos dados do formulário e do resultado do motor. Zero IA. O texto é
    convertido em DOCX formatado pela função _gerar_docx (reuso)."""
    L = []
    L.append("# DIAGNÓSTICO DE RESIDÊNCIA FISCAL BRASIL–EUA")
    L.append("Documento preliminar de triagem — apoio à decisão profissional.\n")

    L.append("## 1. Dados do caso")
    L.append(f"País de residência atual: {form.get('pais_residencia','—')}")
    L.append(f"Data de saída do Brasil: {form.get('data_saida','—')}")
    L.append(f"Tipo de saída: {form.get('tipo_saida','—')}")
    L.append(f"Status migratório nos EUA: {form.get('status_eua','—')}")
    L.append(f"Comunicação de Saída Definitiva: {form.get('csd','—')}")
    L.append(f"Declaração de Saída Definitiva: {form.get('dsd','—')}")
    L.append(f"Empresa no Brasil: {form.get('empresa_brasil','—')}")
    L.append(f"Entidade no exterior: {form.get('entidade_exterior','—')}\n")

    L.append("## 2. Resumo executivo")
    L.append(f"Com base nas informações fornecidas, o caso é classificado como: "
             f"**{diag['classificacao_descricao']}** A pontuação de risco preliminar é "
             f"**{diag['score']}/100 ({diag['faixa_label']})**. Este resultado é uma triagem "
             f"automatizada e não substitui a análise de profissional habilitado.\n")

    L.append("## 3. Linha do tempo fiscal")
    L.append(f"Saída do Brasil informada em: {form.get('data_saida','—')}. "
             f"Retornos ao Brasil: {form.get('retornos','—')}. "
             f"A condição de residência fiscal depende do caráter da saída, do cumprimento "
             f"das obrigações de saída (CSDP/DSDP) e do decurso de 12 meses de ausência.\n")

    L.append("## 4. Classificação preliminar da residência fiscal")
    L.append(diag['classificacao_descricao'] + "\n")

    L.append("## 5. Pontuação de risco")
    L.append(f"{diag['faixa_label']} — {diag['score']} de 100. A pontuação considera a "
             f"situação documental de saída, a coerência das declarações, a existência de "
             f"entidade no exterior, vínculos e rendas no Brasil e ativos no exterior.\n")

    L.append("## 6. Alertas identificados")
    if diag['alertas']:
        for a in diag['alertas']:
            L.append(f"- {a['texto']}")
    else:
        L.append("- Nenhum alerta relevante identificado com os dados informados.")
    L.append("")

    L.append("## 7. Impactos potenciais")
    L.append("Conforme os alertas acima, os principais impactos a investigar envolvem: "
             "tributação de renda mundial enquanto residente fiscal, carnê-leão sobre rendimentos "
             "do exterior, aplicação da Lei 14.754/2023 a entidades controladas, compensação "
             "limitada de imposto pago nos EUA e obrigações acessórias (DSDP, CBE/DCBE).\n")

    L.append("## 8. Providências recomendadas")
    for p in diag['providencias']:
        L.append(f"- {p}")
    L.append("")

    L.append("## 9. Documentos necessários")
    for d in diag['documentos']:
        L.append(f"- {d}")
    L.append("")

    L.append("## 10. Observações para o contador americano")
    L.append("A classificação da entidade para o IRS (disregarded, partnership, corporation) "
             "não define automaticamente o tratamento fiscal brasileiro do sócio. Caso o cliente "
             "ainda seja residente fiscal no Brasil, lucros e rendimentos podem ter reflexos no "
             "Brasil independentemente do tratamento americano.\n")

    L.append("## 11. Observações para o contador brasileiro ou advogado tributarista")
    L.append("Recomenda-se confirmar a data e o caráter da saída, revisar as declarações "
             "entregues, avaliar a regularização da saída fiscal e a aplicação da Lei 14.754/2023, "
             "bem como as obrigações acessórias pertinentes.\n")

    L.append("## 12. Referências legais e fontes")
    fontes = diag['fontes_legais'] or list(FONTES_LEGAIS.values())[:3]
    for f in fontes:
        L.append(f"- {f}")
    L.append("")

    L.append("## 13. Aviso profissional")
    L.append("Este diagnóstico é preliminar, de natureza informativa e de triagem. Não constitui "
             "parecer jurídico ou contábil, não esgota a análise do caso e não substitui a "
             "avaliação de contador, advogado tributarista ou profissional habilitado. As "
             "conclusões dependem da confirmação dos dados e de documentação comprobatória.")
    return "\n".join(L)


def adaptar_transicao(dados: dict, ano_atual: int = 2026) -> dict:
    """Converte os campos do formulário de transição (app.py) para o formato do
    motor. Campos não coletados pelo formulário são deixados ausentes (o motor
    os trata como ausentes). Não usa IA."""
    import re
    txt = str(dados.get("data_saida", ""))
    m = re.search(r"(20\d{2})", txt)
    meses = max(0, (ano_atual - int(m.group(1))) * 12) if m else 0
    tipo = str(dados.get("tipo_saida", ""))
    ent = str(dados.get("entidade_exterior", ""))
    emp = str(dados.get("empresa_brasil", ""))
    bens = str(dados.get("bens_brasil", "")).lower()
    ativos = str(dados.get("ativos_exterior_usd", "")).lower()
    num = re.sub(r"[^\d]", "", ativos.split("milh")[0]) if ativos else ""
    acima_1mi = ("milh" in ativos) or (num.isdigit() and int(num) >= 1_000_000)
    return {
        "saiu_meses": meses,
        "carater_saida": "definitivo" if ("Permanente" in tipo or "Definitiva" in tipo) else "temporario",
        "fez_csdp": dados.get("csd", "").startswith("Sim"),
        "fez_dsdp": dados.get("dsd", "").startswith("Sim"),
        "tem_renda_eua": bool(str(dados.get("rendimentos_exterior", "")).strip()),
        "tem_entidade_exterior": bool(ent) and ent != "Não",
        "tem_llc": "LLC" in ent,
        "tem_mei": "MEI" in emp,
        "socio_simples": "Simples" in emp,
        "renda_brasil": bool(str(dados.get("renda_brasil", "")).strip()),
        "ativos_acima_1mi": acima_1mi,
        "residencia_disponivel_brasil": "imóv" in bens or "imov" in bens,
        "dependentes_brasil": "depend" in bens or "filho" in bens,
        "tem_tax_return": True,  # form não pergunta; não penaliza sem dado
    }


def diagnosticar(respostas: dict) -> dict:
    """Função principal: respostas do wizard -> diagnóstico completo. Zero IA."""
    alertas = _alertas(respostas)
    cat, desc = _classificar(respostas)
    score = _score(respostas, alertas)
    faixa_id, faixa_label = _faixa(score)
    fontes = sorted({a["fonte"] for a in alertas})
    return {
        "versao_motor": VERSAO_MOTOR,
        "classificacao": cat,
        "classificacao_descricao": desc,
        "score": score,
        "faixa": faixa_id,
        "faixa_label": faixa_label,
        "alertas": alertas,
        "providencias": _providencias(respostas, cat),
        "documentos": DOCUMENTOS,
        "perguntas_reuniao": PERGUNTAS_REUNIAO,
        "fontes_legais": fontes,
    }
