import os
import re
import anthropic
import streamlit as st
import pandas as pd
import pdfplumber
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

REGIMES = ["Simples Nacional", "Lucro Presumido", "Lucro Real", "MEI", "Não sei / A definir"]

# ── Módulo Brasil — config por tipo ──────────────────────────────────────────

TIPO_DESCRICOES = {
    "🏢  Diagnóstico Tributário Empresarial": "Análise completa do perfil fiscal de PJ: regime, créditos, riscos e Reforma Tributária.",
    "👤  Check-up Fiscal — Pessoa Física":    "IRPF, carnê-leão, investimentos, malha fina, ganho de capital.",
    "🌾  Produtor Rural / Agronegócio":        "ITR, FUNRURAL, benefícios do agro, impacto da Reforma na cadeia agrícola.",
    "🏛️  Holding Familiar e Sucessória":       "Planejamento patrimonial, ITCMD, antecipação de herança, proteção de ativos.",
    "📊  Planejamento Tributário Estratégico": "Simulação de regimes, reestruturação societária, otimização de carga fiscal.",
    "⚖️  Contencioso Fiscal e Defesas":        "Autos de infração, teses de defesa, estratégia de parcelamento vs. litígio.",
}

TIPO_CONFIG = {
    "🏢  Diagnóstico Tributário Empresarial": {"dre": True,  "avancado": True},
    "👤  Check-up Fiscal — Pessoa Física":    {"dre": False, "avancado": False},
    "🌾  Produtor Rural / Agronegócio":        {"dre": True,  "avancado": True},
    "🏛️  Holding Familiar e Sucessória":       {"dre": False, "avancado": False},
    "📊  Planejamento Tributário Estratégico": {"dre": True,  "avancado": True},
    "⚖️  Contencioso Fiscal e Defesas":        {"dre": False, "avancado": False},
}

# ── System prompts — Módulo Brasil ────────────────────────────────────────────

_BASE = """Você é o MAGUS Fiscal — analista tributário sênior especializado em direito tributário brasileiro, com profundo conhecimento em engenharia tributária, planejamento fiscal lícito e Reforma Tributária.

Você pensa como um advogado tributarista experiente: conhece a complexidade da legislação, o custo da não-conformidade e o valor de um planejamento bem feito. Seu papel é entregar clareza, segurança e ação.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXTO NORMATIVO VIGENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REFORMA TRIBUTÁRIA (EC 132/2023 + LC 214/2025):
- 2026: CBS (0,9%) e IBS (0,1%) em fase de testes. NFs já devem registrar ambos.
- 2027: CBS substitui PIS/COFINS. Imposto Seletivo entra em vigor.
- 2029–2032: Convivência simultânea do sistema antigo com o novo — maior risco de dupla tributação.
- 2033: Extinção de PIS, COFINS, ICMS, ISS e IPI. Somente CBS, IBS e IS vigentes.
- CBS = federal (substitui PIS/COFINS). IBS = estadual/municipal (substitui ICMS/ISS).

NR1 (Portaria MTE nº 1.419/2024): Desde 26/05/2026, fiscalização plenamente punitiva. Empresas sem PGR com riscos psicossociais estão sujeitas a autuação imediata. Custos de adequação são dedutíveis no Lucro Real.

ERROS MAIS COMUNS:
1. Regime tributário inadequado — eleva a carga em até 50%
2. Créditos de PIS/COFINS não aproveitados no Lucro Real
3. Base de cálculo errada no Lucro Presumido (construção civil: 8% vs 32%)
4. ISS recolhido no município errado — LC 116/2003, art. 3º
5. Desoneração da Folha não aplicada — Lei 12.546/2011 / Lei 14.784/2023
6. Mais de 200 incentivos fiscais ativos; empresas deixam R$ 50 bi/ano na mesa
7. Sistemas fiscais desatualizados para CBS/IBS"""

_PRINCIPIOS = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRINCÍPIOS DE CONDUTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Seja técnico mas acessível.
- Nunca omita um risco. Honestidade técnica é o ativo central.
- Estime o impacto financeiro de cada oportunidade identificada.
- Quando a lei for incerta ou controvertida, sinalize claramente.
- Use formatação rica: negrito, tabelas, listas, emojis de risco (🔴🟡🟢)."""

_EST_EMPRESARIAL = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — DIAGNÓSTICO TRIBUTÁRIO EMPRESARIAL

**Empresa:** [setor]  **Regime:** [regime]  **Faturamento:** [valor]  **Data:** [mês/ano]

---
## 1. RESUMO DA SITUAÇÃO
Síntese do perfil tributário. O que é mais urgente dado o momento atual.

---
## 2. CRÉDITOS E RECUPERAÇÃO TRIBUTÁRIA
Para cada crédito: nome, base legal, relevância (Alta/Média/Baixa) e observação prática.

---
## 3. RISCOS FISCAIS IDENTIFICADOS
🔴 Alto | 🟡 Médio | 🟢 Baixo. Para cada risco: descrição, base legal, consequência e o que verificar.

---
## 4. IMPACTO DA REFORMA TRIBUTÁRIA
Curto prazo (2026–2027) / Médio prazo (2028–2032) / Antes de 2027. Sistema de NF preparado para CBS/IBS?

---
## 5. ALERTA NR1
Se houver funcionários CLT: PGR atualizado? Custo de adequação (dedutível no LR)? Contingência passiva?

---
## 6. OPORTUNIDADES DE PLANEJAMENTO
Oportunidades de redução lícita da carga, por ordem de impacto. O que fazer, base legal e impacto estimado.

---
## 7. RECOMENDAÇÃO DE REGIME TRIBUTÁRIO
Compare Simples / Presumido / Real com estimativas numéricas. Recomende e justifique.

---
## 8. PLANO DE AÇÃO PRIORIZADO
**⚡ Próximos 30 dias** | **📅 Próximos 6 meses** | **🔭 Antes de 2027**

---
## 9. ESBOÇO DE PARECER PRELIMINAR
2–3 parágrafos em linguagem jurídica, prontos para uso como base de parecer formal.

---
## 10. PRÓXIMAS PERGUNTAS E DOCUMENTOS NECESSÁRIOS
Nome do documento, período e finalidade."""

_EST_PF = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — CHECK-UP FISCAL PESSOA FÍSICA

**Declarante:** [profissão]  **Renda Anual:** [valor]  **Data:** [mês/ano]

---
## 1. PERFIL FISCAL DO DECLARANTE
Categoria de contribuinte, obrigações principais, complexidade da situação.

---
## 2. INCONSISTÊNCIAS E RISCOS DE MALHA FINA
🔴 Alto | 🟡 Médio | 🟢 Baixo. Para cada risco: o que é, o que a Receita cruza e o que providenciar.

---
## 3. DEDUÇÕES LEGAIS — APROVEITAMENTO E OPORTUNIDADES
Deduções disponíveis (saúde, educação, previdência, dependentes, livro-caixa). O que pode estar sendo perdido e impacto estimado em R$.

---
## 4. RENDIMENTOS DE CAPITAL E INVESTIMENTOS
Tributação de cada tipo de investimento. Erros comuns de declaração. Alíquotas aplicáveis.

---
## 5. GANHO DE CAPITAL
Imóveis, ações, cotas, criptoativos. Obrigações, prazos de GCAP, oportunidades de isenção.

---
## 6. CARNÊ-LEÃO E RECOLHIMENTOS MENSAIS
Rendimentos sujeitos a carnê-leão. Está recolhendo corretamente? Necessidade de retificação?

---
## 7. IMPACTO DA REFORMA TRIBUTÁRIA (se aplicável)
Mudanças que afetam investimentos, dividendos de PJ controlada ou rendimentos do declarante.

---
## 8. PLANO DE AÇÃO
**⚡ Antes do prazo da declaração** | **📅 Ao longo do ano fiscal**

---
## 9. DOCUMENTOS NECESSÁRIOS
O que o profissional precisa do cliente para aprofundar a análise."""

_EST_RURAL = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — ANÁLISE TRIBUTÁRIA AGRONEGÓCIO

**Produtor:** [atividade]  **Perfil:** [PF rural / PJ / Cooperativa]  **Faturamento:** [valor]  **Data:** [mês/ano]

---
## 1. PERFIL DO PRODUTOR RURAL
Atividade, regime atual, obrigações principais e pontos de atenção imediatos.

---
## 2. REGIME MAIS VANTAJOSO
Compare PF Rural (Livro Caixa + IR 27,5%) vs. PJ Agronegócio (Presumido/Real) vs. Cooperativa. Com estimativas de carga para o faturamento informado.

---
## 3. FUNRURAL E CONTRIBUIÇÃO PREVIDENCIÁRIA RURAL
Alíquota aplicável. Está recolhendo corretamente? Possibilidade de recuperação de valores pagos a maior.

---
## 4. CRÉDITOS E RECUPERAÇÃO TRIBUTÁRIA
PIS/COFINS agropecuários, ICMS diferido, créditos de insumos. Base legal, relevância e observação.

---
## 5. RISCOS FISCAIS IDENTIFICADOS
🔴 Alto | 🟡 Médio | 🟢 Baixo. Foco em ITR, FUNRURAL, obrigações acessórias rurais.

---
## 6. BENEFÍCIOS FISCAIS DO AGRONEGÓCIO
Isenções de IPI/ICMS em máquinas e insumos, PRONAMP, isenção de IRPF para PF rural no limite legal.

---
## 7. IMPACTO DA REFORMA TRIBUTÁRIA NO AGRO
Exportações (imunidade CBS/IBS), Imposto Seletivo sobre defensivos, cashback para produtor, calendário.

---
## 8. PLANO DE AÇÃO
**⚡ Próximos 30 dias** | **📅 Próximos 6 meses** | **🔭 Antes de 2027**

---
## 9. DOCUMENTOS E INFORMAÇÕES NECESSÁRIOS"""

_EST_HOLDING = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — PLANEJAMENTO PATRIMONIAL E HOLDING

**Tipo:** [tipo de holding]  **Patrimônio:** [valor]  **Data:** [mês/ano]

---
## 1. ESTRUTURA PATRIMONIAL ANALISADA
Síntese do patrimônio descrito, tipo de holding mais adequado e objetivo central.

---
## 2. HOLDING vs. TITULARIDADE DIRETA — COMPARATIVO
Tabela: tributação de renda, proteção patrimonial, custo de sucessão e custo de manutenção.

---
## 3. ITCMD — ANÁLISE POR ESTADO
Alíquota e base de cálculo nos estados indicados. Oportunidades: transmissão de quotas vs. bens, doação com reserva de usufruto.

---
## 4. GESTÃO DA RENDA DOS SÓCIOS
Comparativo: pró-labore vs. dividendos vs. retirada de capital. Carga tributária de cada alternativa.

---
## 5. BLINDAGEM PATRIMONIAL — O QUE É LÍCITO
Cláusulas de impenhorabilidade, incomunicabilidade, reversão. Linha entre planejamento e fraude.

---
## 6. RISCOS IDENTIFICADOS
🔴 Alto | 🟡 Médio | 🟢 Baixo — riscos jurídicos, tributários e sucessórios.

---
## 7. ESTRATÉGIA SUCESSÓRIA RECOMENDADA
Sequência: constituição da holding, integralização, doação com usufruto ou testamento. Cronograma ideal.

---
## 8. IMPACTO DA REFORMA TRIBUTÁRIA
ITCMD progressivo em debate, possível tributação de dividendos, ITBI na integralização. Distinguir lei de projeto.

---
## 9. PLANO DE AÇÃO
**⚡ Próximos 30 dias** | **📅 Próximos 6 meses** | **🔭 Longo prazo**

---
## 10. DOCUMENTOS E DUE DILIGENCE NECESSÁRIOS"""

_EST_ESTRATEGICO = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — PLANEJAMENTO TRIBUTÁRIO ESTRATÉGICO

**Empresa:** [setor]  **Regime Atual:** [regime]  **Faturamento:** [valor]  **Data:** [mês/ano]

---
## 1. DIAGNÓSTICO ATUAL
O que está correto, o que está abaixo do ideal e qual é a maior oportunidade.

---
## 2. SIMULAÇÃO DE REGIMES TRIBUTÁRIOS
| Regime | Carga Estimada (R$) | % do Faturamento | Recomendado? |
|---|---|---|---|
| Simples Nacional | | | |
| Lucro Presumido | | | |
| Lucro Real | | | |

---
## 3. CARGA PROJETADA — 3 CENÁRIOS
Com base nas projeções de faturamento informadas:
| Cenário | Faturamento | Regime Ideal | Carga (R$) | Economia vs. Atual |
|---|---|---|---|---|
| Conservador | | | | |
| Realista | | | | |
| Otimista | | | | |

---
## 4. OPORTUNIDADES DE REESTRUTURAÇÃO
Reestruturação societária, split de atividades, benefícios regionais/setoriais. Impacto estimado e viabilidade.

---
## 5. BENEFÍCIOS FISCAIS DISPONÍVEIS
Incentivos aplicáveis ao setor e região. Custo-benefício e prazo para aproveitar.

---
## 6. IMPACTO DA REFORMA TRIBUTÁRIA — CRONOGRAMA DE AÇÃO
O que fazer antes de 2027 / durante 2027–2032 / o que estará resolvido em 2033. Decisões que NÃO podem esperar.

---
## 7. RISCOS DA MUDANÇA DE ESTRATÉGIA
🔴 Alto | 🟡 Médio | 🟢 Baixo — riscos de transição, carências, obrigações acessórias.

---
## 8. PLANO DE IMPLEMENTAÇÃO
**⚡ Imediato (30 dias)** | **📅 6 meses** | **🔭 Antes de 2027**

---
## 9. DOCUMENTOS NECESSÁRIOS"""

_EST_CONTENCIOSO = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — CONTENCIOSO FISCAL E DEFESAS

**Tributo:** [tributo]  **Esfera:** [admin/judicial]  **Valor:** [valor]  **Data:** [mês/ano]

---
## 1. SÍNTESE DO CASO
O que está sendo questionado, valor com atualização estimada, fase atual e prazo crítico mais próximo.

---
## 2. ANÁLISE JURÍDICA E BASE LEGAL
Fundamento da autuação. Legalidade e constitucionalidade da exigência. Pontos fracos da posição do Fisco.

---
## 3. TESES DE DEFESA DISPONÍVEIS
Para cada tese: fundamento legal/constitucional, força jurídica e observações. Ordene por probabilidade de êxito.

---
## 4. JURISPRUDÊNCIA RELEVANTE
**CARF:** tendência atual da câmara competente
**STJ:** precedentes vinculantes ou relevantes
**STF:** repercussão geral ou ADI relacionada
Indique se a tendência é favorável ou desfavorável ao contribuinte.

---
## 5. AVALIAÇÃO DE RISCO E PROBABILIDADE DE ÊXITO
🔴 Risco alto — tese fraca, jurisprudência desfavorável
🟡 Risco moderado — questão em aberto ou divergente
🟢 Boa perspectiva — tese forte, precedentes favoráveis
Inclua estimativa percentual de êxito se possível.

---
## 6. ESTRATÉGIA RECOMENDADA
Compare: defesa administrativa (DRJ/CARF), mandado de segurança, ação anulatória, parcelamento, transação tributária. Recomende e justifique.

---
## 7. IMPACTO FINANCEIRO E PROVISÕES CONTÁBEIS
Valor atualizado com multa e juros SELIC. Necessidade de provisão (CPC 25). Impacto no resultado e no regime.

---
## 8. PLANO DE AÇÃO E PRAZOS CRÍTICOS
Cada prazo processual relevante e a ação correspondente. Destacar o que vence primeiro.

---
## 9. DOCUMENTOS E PROVAS NECESSÁRIOS"""

_ESTRUTURAS = {
    "🏢  Diagnóstico Tributário Empresarial": _EST_EMPRESARIAL,
    "👤  Check-up Fiscal — Pessoa Física":    _EST_PF,
    "🌾  Produtor Rural / Agronegócio":        _EST_RURAL,
    "🏛️  Holding Familiar e Sucessória":       _EST_HOLDING,
    "📊  Planejamento Tributário Estratégico": _EST_ESTRATEGICO,
    "⚖️  Contencioso Fiscal e Defesas":        _EST_CONTENCIOSO,
}

# ── System prompt — Módulo Transição Brasil → EUA ─────────────────────────────

_BASE_TRANSICAO = """Você é o MAGUS Fiscal — especialista em tributação bilateral Brasil-EUA, com profundo conhecimento em:
- Residência fiscal brasileira e regras de saída definitiva (CSD e DSD)
- Carnê-leão sobre rendimentos recebidos do exterior (Regulamento do IR, art. 53)
- Lei 14.754/2023 e IN RFB 2.180/2024 (tributação de entidades no exterior — LLCs, trusts, offshores)
- CBE/DCBE (declaração de capitais brasileiros no exterior — Banco Central do Brasil)
- Simples Nacional e vedação para não residentes (LC 123/2006, art. 17, II)
- FATCA (Decreto 8.506/2015) e troca automática de informações Brasil-EUA
- Solução de Consulta Cosit nº 56/2026 (classificação fiscal de LLCs nos EUA)
- IN RFB nº 1.037/2010 (regimes fiscais privilegiados — LLC com sócios não residentes nos EUA)
- Perguntas e Respostas IRPF 2026 (especialmente questões 125, 130, 140 e 142)
- Substantial Presence Test (lado americano) e suas implicações para a residência fiscal dupla

Você pensa como um advogado tributarista sênior com experiência bilateral. Conhece:
- O risco da dupla residência fiscal (tributado no Brasil E nos EUA ao mesmo tempo)
- As armadilhas do carnê-leão não recolhido (multa de 75% + juros SELIC + representação fiscal)
- As novas regras de LLC sob a Lei 14.754/2023 (lucro tributado mesmo sem distribuição)
- A gravidade das multas por descumprimento de CBE (R$ 25.000 a R$ 250.000)
- A vedação do Simples Nacional para sócios domiciliados no exterior (risco de exclusão retroativa)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REGRAS DE RESIDÊNCIA FISCAL BRASILEIRA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REGRA 1 — SAÍDA FORMALIZADA:
Se houve saída permanente E CSD (Comunicação de Saída Definitiva) + DSD (Declaração de Saída Definitiva) foram apresentados corretamente → classificar como PROVÁVEL NÃO RESIDENTE a partir da data informada na CSD.

REGRA 2 — SAÍDA NÃO FORMALIZADA, MAS LONGA:
Sem CSD/DSD, mas ausência consecutiva superior a 12 meses → classificar como PROVÁVEL NÃO RESIDENTE a partir do dia seguinte ao 12º mês de ausência consecutiva. MAS: marcar RISCO DOCUMENTAL ALTO — a Receita pode questionar o período de residência e exigir IR sobre todo o período não declarado.

REGRA 3 — AUSÊNCIA CURTA SEM FORMALIZAÇÃO:
Sem CSD/DSD e menos de 12 meses de ausência consecutiva → AINDA É RESIDENTE FISCAL BRASILEIRO. Obrigações plenas: IRPF anual, carnê-leão mensal, GCAP, CBE se aplicável.

REGRA 4 — RETORNOS AO BRASIL:
Retornos ao Brasil podem interromper a contagem de ausência consecutiva. Se houve retorno por mais de 30 dias consecutivos, reinicia a contagem. Analisar com cuidado.

REGRA 5 — VÍNCULOS FORTES:
Manutenção de vínculos fortes (empresa ativa como titular/sócio majoritário, fonte pagadora, imóvel residencial como domicílio principal) pode indicar residência fiscal mesmo após saída, mesmo com CSD/DSD — jurisprudência administrativa em formação.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CARNÊ-LEÃO 2025 — TABELA PROGRESSIVA MENSAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Base de Cálculo Mensal (R$) | Alíquota | Parcela a Deduzir (R$) |
|---|---|---|
| Até 2.259,20 | Isento | — |
| De 2.259,21 a 2.826,65 | 7,5% | 169,44 |
| De 2.826,66 a 3.751,05 | 15% | 381,44 |
| De 3.751,06 a 4.664,68 | 22,5% | 662,77 |
| Acima de 4.664,68 | 27,5% | 896,00 |

CÂMBIO: usar PTAX do último dia útil do mês de recebimento (tabela do Banco Central). Para estimativas, usar câmbio informado pelo usuário.
COMPENSAÇÃO: imposto pago no exterior pode ser compensado, limitado ao imposto calculado no Brasil para aquela renda.
PRAZO: recolhimento mensal via DARF, código 0190, até o último dia útil do mês seguinte ao recebimento.
PENALIDADE POR ATRASO: multa de 75% (150% se fraude) + juros SELIC. Representação fiscal para fins penais se valor superar R$ 2,5 milhões.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEI 14.754/2023 — ENTIDADES NO EXTERIOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Vigência: 01/01/2024. Regulamentada pela IN RFB 2.180/2024.

LLC DISREGARDED ENTITY (sócio único) com sócio RESIDENTE no Brasil:
- Lucros tributados pelo IRPF à alíquota de 27,5% sobre o lucro contábil anual
- Tributação ocorre em 31/12 de cada ano, MESMO SEM DISTRIBUIÇÃO
- Imposto via DARF, prazo até 31 de maio do ano seguinte
- Obrigação de informar na DIRPF: balanço em reais, lucro/prejuízo, distribuições

SC COSIT 56/2026:
- LLC transparente com sócios não residentes nos EUA pode ser classificada como regime fiscal privilegiado conforme IN RFB 1.037/2010
- Tributação diferenciada e obrigações acessórias adicionais se aplicável

ALERTA DE NÃO RESIDENTE:
- Se o sócio da LLC foi classificado como NÃO RESIDENTE fiscal brasileiro → a Lei 14.754/2023 pode não se aplicar para o período posterior à perda da residência
- MAS: o período anterior à perda de residência pode ainda gerar obrigação fiscal se os lucros não foram declarados

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CBE/DCBE — BANCO CENTRAL DO BRASIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OBRIGAÇÃO ANUAL:
- Residente brasileiro com ativos no exterior em 31/12 >= US$ 1.000.000 → CBE anual obrigatória
- Prazo: até 05 de abril do ano seguinte

OBRIGAÇÃO TRIMESTRAL:
- Ativos no exterior em qualquer data base trimestral >= US$ 100.000.000 → CBE trimestral

ATIVOS QUE DEVEM SER DECLARADOS:
Contas bancárias, corretoras/brokerage accounts, imóveis, participação em LLCs e empresas, criptoativos, empréstimos a receber no exterior, outros ativos financeiros.

PENALIDADES:
- Não entrega: multa de R$ 25.000 a R$ 250.000 (resolução BCB 278/2022)
- Declaração incorreta: multa adicional proporcional ao valor omitido
- Sem prescrição enquanto a omissão não for regularizada

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIMPLES NACIONAL E NÃO RESIDENTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LC 123/2006, art. 17, II: É vedada a opção pelo Simples Nacional à empresa cujo titular ou sócio seja domiciliado no exterior.

Se o usuário for classificado como não residente ou domiciliado no exterior:
- Gerar ALERTA OBRIGATÓRIO sobre o enquadramento da empresa brasileira no Simples
- Não concluir automaticamente exclusão — gerar alerta para revisão profissional urgente
- Risco: exclusão retroativa com lançamento da diferença de tributos em regime normal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FATCA E TROCA AUTOMÁTICA DE INFORMAÇÕES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Decreto 8.506/2015: Brasil e EUA trocam informações financeiras automaticamente via FATCA
- Contas bancárias e de investimento no Brasil de pessoas com vínculo com os EUA (green card, cidadania, substantial presence) são reportadas ao IRS americano
- Contas nos EUA de brasileiros são reportadas à Receita Federal brasileira
- Implicação prática: omissões fiscais bilaterais têm alta probabilidade de detecção cruzada"""

_EST_TRANSICAO = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA DE RESPOSTA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# MAGUS FISCAL — SAÍDA FISCAL BRASIL → EUA

**Residente em:** [país]  **Data de Saída:** [data]  **Tipo:** [permanente/temporária]  **Data da Análise:** [mês/ano]

---
## 1. RESUMO EXECUTIVO
Síntese objetiva da situação fiscal bilateral. O que é mais urgente. Nível geral de risco.

---
## 2. STATUS DE RESIDÊNCIA FISCAL BRASILEIRA

**Classificação:** 🔴 PROVÁVEL RESIDENTE | 🟡 PERÍODO DE TRANSIÇÃO / RISCO DOCUMENTAL | 🟢 PROVÁVEL NÃO RESIDENTE | ⚪ REQUER REVISÃO PROFISSIONAL

Fundamento legal da classificação. Datas-chave relevantes. O que está faltando para formalizar a saída. Riscos de manter o status atual.

---
## 3. DASHBOARD DE RISCOS FISCAIS

| Área | Situação Identificada | Nível |
|---|---|---|
| Residência fiscal brasileira | | 🔴/🟡/🟢 |
| Carnê-leão (rendimentos exterior) | | 🔴/🟡/🟢 |
| LLC / Entidade no exterior | | 🔴/🟡/🟢 |
| CBE/DCBE (Banco Central) | | 🔴/🟡/🟢 |
| Empresa brasileira (Simples/MEI) | | 🔴/🟡/🟢 |
| FATCA / Troca de informações | | 🔴/🟡/🟢 |
| Documentação faltante | | 🔴/🟡/🟢 |

---
## 4. CARNÊ-LEÃO — ANÁLISE PRELIMINAR
Existe obrigação de recolhimento? Qual período está em aberto? Se informados valores de renda: estimativa mensal preliminar com aplicação da tabela progressiva (converter para reais pelo câmbio informado ou estimado). Risco de multa e juros acumulados. O que precisa ser regularizado e como.

---
## 5. LLC E ENTIDADES NO EXTERIOR
Classificação da entidade informada. Análise sob a Lei 14.754/2023 e IN RFB 2.180/2024. SC Cosit 56/2026 e IN RFB 1.037/2010 — risco de regime privilegiado. Obrigações de declaração e pagamento. Período de tributação aplicável. Alertas específicos.

---
## 6. CBE/DCBE — CAPITAIS BRASILEIROS NO EXTERIOR
Existe obrigação de declarar ao Banco Central? Threshold aplicável ao caso. Quais ativos devem ser declarados. Penalidade estimada pelo descumprimento. Como regularizar.

---
## 7. EMPRESA BRASILEIRA — ANÁLISE LC 123/2006
Se houver MEI ou empresa no Simples Nacional: análise direta da vedação para sócios domiciliados no exterior. Risco de exclusão retroativa. O que deve ser avaliado com profissional urgentemente.

---
## 8. CHECKLIST DE DOCUMENTOS
Lista prática de documentos necessários para regularização completa, separados por área:
- Para a saída fiscal (RFB)
- Para o carnê-leão (se aplicável)
- Para LLC/entidade (se aplicável)
- Para CBE (Banco Central, se aplicável)
- Para a empresa brasileira (se aplicável)
- Para coordenação com contador americano

---
## 9. MEMO FOR U.S. ACCOUNTANT
*[This section is written in English for coordination with the U.S.-based tax professional]*

**Key Brazilian Tax Considerations — Client Relocating to the United States**

**Brazilian Tax Residency:**
- Brazilian tax residency does not automatically end upon physical relocation. Two formal documents are required: the Comunicação de Saída Definitiva do País (CSD) and the Declaração de Saída Definitiva do País (DSD). Without these, Brazilian tax obligations may continue for up to 12 months of consecutive absence, and potentially longer.
- Please request confirmation of whether these documents were filed, and on what dates.

**Continuing Brazilian Tax Obligations:**
- If the client was a Brazilian tax resident during any part of the year, Brazilian income tax (IRPF) and carnê-leão obligations apply to worldwide income during that period.
- Carnê-leão is a monthly self-assessed tax on income received from foreign sources by Brazilian residents — not withheld at source. Failure to collect is subject to 75% penalty plus SELIC interest.

**U.S. LLC and Brazilian Tax Treatment:**
- A U.S. LLC classified as a disregarded entity for U.S. federal tax purposes is NOT automatically treated as transparent under Brazilian tax law.
- Under Lei 14.754/2023 (effective 01/01/2024), Brazilian tax residents who own or control foreign entities are subject to annual taxation on the entity's accounting profits at 27.5%, even without actual distribution.
- SC Cosit 56/2026 may classify certain LLCs with non-U.S.-resident members as entities in a privileged tax jurisdiction — additional Brazilian reporting obligations may apply.

**No Full Tax Treaty:**
- Brazil and the United States do not have a comprehensive income tax treaty. Foreign tax credits are available under domestic Brazilian law but with limitations. Timing differences and income characterization mismatches should be reviewed carefully.

**FATCA and Information Exchange:**
- Brazil and the U.S. exchange financial account information automatically under the FATCA agreement (Decree 8.506/2015). Brazilian financial institutions report accounts of U.S. persons to the IRS; U.S. financial institutions report Brazilian residents' accounts to Receita Federal. Coordination is essential.

**Recommended Coordination Points:**
1. Confirm Brazilian tax residency status and effective exit date.
2. Determine whether CSD and DSD were filed, and on what dates.
3. Assess carnê-leão exposure for periods of Brazilian tax residency.
4. Analyze LLC treatment under Lei 14.754/2023 for periods of Brazilian residency.
5. Review CBE (Banco Central) reporting obligations for foreign assets.
6. Coordinate FBAR/FATCA filings with Brazilian DIRPF and CBE filings to ensure consistency.

---
## 10. PRÓXIMOS PASSOS

**⚡ Imediato (próximos 30 dias)** — O que não pode esperar

**📅 Próximos 3 meses** — Regularização e compliance

**🔭 Longo prazo** — Estruturação e planejamento

---
*AVISO IMPORTANTE: Esta análise é preliminar e educacional. Os cálculos são estimativas baseadas nas informações fornecidas e não substituem aconselhamento profissional. Situações com múltiplas jurisdições, entidades no exterior, omissões fiscais anteriores ou status jurídico incerto exigem revisão por advogado tributarista e/ou contador especializado em tributação internacional. A MAGUS Fiscal não se responsabiliza por decisões tomadas com base exclusiva nesta análise.*"""


def build_system_prompt(tipo, modulo="brasil"):
    if modulo == "transicao":
        return _BASE_TRANSICAO + "\n" + _EST_TRANSICAO + _PRINCIPIOS
    estrutura = _ESTRUTURAS.get(tipo, _EST_EMPRESARIAL)
    return _BASE + "\n" + estrutura + _PRINCIPIOS


# ── Formulários — Módulo Brasil ────────────────────────────────────────────────

def _form_empresarial():
    dados = {}
    c1, c2 = st.columns(2)
    with c1:
        dados["setor"] = st.text_input("Setor / Segmento", placeholder="Ex: Construção civil, Comércio varejista, Serviços de TI...")
        dados["regime"] = st.selectbox("Regime Tributário Atual", REGIMES)
        dados["faturamento"] = st.text_input("Faturamento Anual Aproximado", placeholder="Ex: R$ 2 milhões, R$ 500 mil...")
    with c2:
        dados["atividades"] = st.text_area("Descrição das Atividades", placeholder="O que a empresa faz, como opera, principais clientes...", height=130)
        dados["questao"] = st.text_area("Dúvida ou Objetivo Específico", placeholder="O que você quer investigar ou resolver?", height=130)
    ok = bool(dados["setor"] and dados["atividades"] and dados["questao"])
    return dados, ok


def _form_pf():
    dados = {}
    c1, c2 = st.columns(2)
    with c1:
        dados["profissao"] = st.text_input("Profissão / Ocupação principal", placeholder="Ex: Médico autônomo, Advogado sócio, Servidor público...")
        dados["renda_anual"] = st.text_input("Renda bruta anual total aproximada", placeholder="Ex: R$ 350 mil, R$ 800 mil...")
        dados["estado_civil"] = st.selectbox("Estado civil", ["Solteiro(a)", "Casado(a) / União estável", "Divorciado(a)", "Viúvo(a)"])
        dados["tem_imoveis"] = st.selectbox("Possui imóveis para declarar?", ["Não", "Sim — 1 imóvel", "Sim — 2 ou mais imóveis"])
    with c2:
        dados["fontes_renda"] = st.text_area("Fontes de renda — descreva cada uma", placeholder="Ex: salário CLT R$ 15k/mês, consultório autônomo R$ 10k/mês, aluguéis R$ 5k/mês...", height=110)
        dados["investimentos"] = st.text_input("Investimentos (se houver)", placeholder="Ex: renda fixa, ações, FII, previdência privada, criptoativos...")
        dados["questao"] = st.text_area("Dúvida ou Objetivo Específico", placeholder="Ex: Risco de malha fina, otimizar deduções, declarar ganho de capital...", height=100)
    ok = bool(dados["profissao"] and dados["fontes_renda"] and dados["questao"])
    return dados, ok


def _form_rural():
    dados = {}
    c1, c2 = st.columns(2)
    with c1:
        dados["tipo_atividade"] = st.text_input("Tipo de atividade rural", placeholder="Ex: Lavoura de soja, Pecuária bovina, Avicultura, Aquicultura...")
        dados["perfil"] = st.selectbox("Perfil do produtor", ["PF Rural (pessoa física)", "PJ Agronegócio", "Cooperativa agropecuária", "Integração / Parceria"])
        dados["faturamento"] = st.text_input("Faturamento bruto rural anual", placeholder="Ex: R$ 1,5 milhão, R$ 8 milhões...")
        dados["exporta"] = st.selectbox("Exporta produção?", ["Não", "Sim — exportação direta", "Sim — via trading/cooperativa"])
        dados["funcionarios_rurais"] = st.text_input("Nº de trabalhadores rurais (para FUNRURAL)", placeholder="Ex: 15")
    with c2:
        dados["atividades"] = st.text_area("Descrição das atividades e operação", placeholder="Como opera, principais culturas/rebanho, sazonalidade, armazenamento...", height=130)
        dados["questao"] = st.text_area("Dúvida ou Objetivo Específico", placeholder="Ex: Verificar FUNRURAL, avaliar mudança para PJ, recuperar créditos de insumos...", height=130)
    ok = bool(dados["tipo_atividade"] and dados["atividades"] and dados["questao"])
    return dados, ok


def _form_holding():
    dados = {}
    c1, c2 = st.columns(2)
    with c1:
        dados["tipo_holding"] = st.selectbox("Tipo de holding", ["Holding Pura (participações)", "Holding Mista (participações + atividade operacional)", "Holding Patrimonial (imóveis)", "Holding Familiar (sucessória)"])
        dados["patrimonio"] = st.text_input("Patrimônio total estimado", placeholder="Ex: R$ 5 milhões, R$ 20 milhões...")
        dados["estado_bens"] = st.text_input("Estado(s) onde estão os bens e a sede", placeholder="Ex: Goiás, São Paulo e Minas Gerais")
        dados["num_herdeiros"] = st.text_input("Número de herdeiros / sócios familiares", placeholder="Ex: 3 filhos + cônjuge")
    with c2:
        dados["descricao"] = st.text_area("Descrição do patrimônio e objetivos", placeholder="Ex: 4 imóveis comerciais, participação em 2 empresas, fazenda. Objetivo: proteger e preparar sucessão...", height=130)
        dados["questao"] = st.text_area("Dúvida ou Objetivo Específico", placeholder="Ex: Vale a pena criar a holding agora? Qual o impacto do ITCMD? Como minimizar o custo da sucessão?", height=130)
    ok = bool(dados["patrimonio"] and dados["descricao"] and dados["questao"])
    return dados, ok


def _form_estrategico():
    dados = {}
    c1, c2 = st.columns(2)
    with c1:
        dados["setor"] = st.text_input("Setor / Segmento", placeholder="Ex: Serviços de TI, Indústria alimentícia...")
        dados["regime"] = st.selectbox("Regime Tributário Atual", REGIMES)
        dados["faturamento"] = st.text_input("Faturamento Atual", placeholder="Ex: R$ 3,5 milhões...")
        dados["margem_lucro"] = st.text_input("Margem de lucro real estimada", placeholder="Ex: 12%, 8%, 25%")
        dados["num_funcionarios"] = st.text_input("Número de funcionários", placeholder="Ex: 28")
        dados["folha_mensal"] = st.text_input("Folha de pagamento mensal", placeholder="Ex: R$ 180 mil")
    with c2:
        dados["objetivo"] = st.text_area("Objetivo do planejamento", placeholder="Ex: Reduzir carga antes de 2027, avaliar abertura de filial, estudar mudança de regime...", height=110)
        dados["questao"] = st.text_area("Decisão específica a tomar", placeholder="Ex: Vale mudar para Lucro Real agora? Qual regime será melhor após a Reforma?", height=120)
    ok = bool(dados["setor"] and dados["objetivo"] and dados["questao"])
    return dados, ok


def _form_contencioso():
    dados = {}
    c1, c2 = st.columns(2)
    with c1:
        dados["setor"] = st.text_input("Setor / Segmento", placeholder="Ex: Comércio varejista, Prestação de serviços...")
        dados["regime"] = st.selectbox("Regime Tributário", REGIMES)
        dados["tributo"] = st.selectbox("Tributo em discussão", ["IRPJ / CSLL", "PIS / COFINS", "ISS", "ICMS", "Contribuições Previdenciárias (INSS/CPRB)", "ITBI / ITCMD", "IOF", "IPI", "Múltiplos tributos", "Outro"])
        dados["esfera"] = st.selectbox("Esfera processual", ["Administrativo — DRJ (1ª instância)", "Administrativo — CARF (2ª instância)", "Judicial — 1ª instância", "Judicial — TRF / Recursal", "Preventivo / Consultivo", "Transação tributária"])
        dados["valor_envolvido"] = st.text_input("Valor estimado em discussão", placeholder="Ex: R$ 450 mil, R$ 2 milhões...")
    with c2:
        dados["descricao"] = st.text_area("Descrição do caso / auto de infração / questão jurídica", placeholder="Descreva o que a Receita autuou ou a questão tributária que precisa resolver...", height=130)
        dados["questao"] = st.text_area("Objetivo / O que precisa decidir", placeholder="Ex: Vale contestar ou parcelar? Quais são as teses disponíveis? Preciso de liminar?", height=100)
    ok = bool(dados["tributo"] and dados["descricao"] and dados["questao"])
    return dados, ok


# ── Formulário — Módulo Transição Brasil → EUA ────────────────────────────────

def _form_transicao():
    dados = {}

    c1, c2, c3 = st.columns(3)
    with c1:
        dados["pais_residencia"] = st.text_input(
            "País atual de residência",
            placeholder="Ex: Estados Unidos"
        )
        dados["data_saida"] = st.text_input(
            "Data aproximada de saída do Brasil",
            placeholder="Ex: junho de 2022, 15/03/2023..."
        )
        dados["tipo_saida"] = st.selectbox("Tipo de saída do Brasil", [
            "Permanente / Definitiva",
            "Temporária (prazo determinado)",
            "Indefinida / Não formalizada"
        ])
    with c2:
        dados["csd"] = st.selectbox("Comunicação de Saída Definitiva (CSD)?", [
            "Não apresentou",
            "Sim — apresentou",
            "Não sabe"
        ])
        dados["dsd"] = st.selectbox("Declaração de Saída Definitiva (DSD)?", [
            "Não apresentou",
            "Sim — apresentou",
            "Não sabe"
        ])
        dados["retornos"] = st.selectbox("Retornou ao Brasil após a saída?", [
            "Não retornou",
            "Sim — visitas curtas (menos de 30 dias por viagem)",
            "Sim — visitas longas (mais de 30 dias em alguma viagem)",
            "Sim — ficou mais de 183 dias em algum ano-calendário"
        ])
    with c3:
        dados["status_eua"] = st.selectbox("Status migratório nos EUA", [
            "Cidadão americano (naturalizado ou nato)",
            "Green Card (residente permanente)",
            "Visto de trabalho (H-1B, L-1, O-1)",
            "Visto de investidor (EB-5)",
            "Outro visto temporário",
            "Substantial Presence Test atingido",
            "Status incerto / sob análise"
        ])
        dados["empresa_brasil"] = st.selectbox("Mantém empresa no Brasil?", [
            "Não",
            "Sim — MEI",
            "Sim — empresa no Simples Nacional",
            "Sim — empresa no Lucro Presumido ou Real"
        ])

    st.markdown("")

    r1, r2 = st.columns(2)
    with r1:
        dados["rendimentos_exterior"] = st.text_area(
            "Rendimentos no exterior — descreva cada fonte",
            placeholder="Ex: salário W-2 US$ 120k/ano, LLC com lucro US$ 50k/ano, dividendos US$ 5k, trabalho autônomo 1099 US$ 30k...",
            height=100
        )
        dados["entidade_exterior"] = st.selectbox("Possui LLC ou empresa no exterior?", [
            "Não",
            "Sim — LLC (sócio único — disregarded entity)",
            "Sim — LLC (múltiplos sócios — partnership)",
            "Sim — C-Corporation",
            "Sim — Trust",
            "Sim — outra estrutura"
        ])
        dados["ativos_exterior_usd"] = st.text_input(
            "Total aproximado de ativos no exterior (em US$)",
            placeholder="Ex: US$ 500.000, US$ 1,2 milhão, US$ 3 milhões..."
        )
    with r2:
        dados["bens_brasil"] = st.text_area(
            "Bens e vínculos mantidos no Brasil (descreva)",
            placeholder="Ex: imóvel residencial alugado, conta no Bradesco, corretora XP, dependentes (filhos menores), empresa ativa...",
            height=100
        )
        dados["renda_brasil"] = st.text_input(
            "Rendimentos de fonte brasileira (se houver)",
            placeholder="Ex: aluguel R$ 5k/mês, dividendos de empresa brasileira R$ 20k/ano..."
        )
        dados["questao"] = st.text_area(
            "Dúvida ou objetivo principal",
            placeholder="Ex: Quero regularizar minha saída fiscal. Tenho LLC e não sei se devo declarar no Brasil. Preciso entender o carnê-leão e se minha empresa pode ficar no Simples...",
            height=110
        )

    ok = bool(dados.get("pais_residencia") and dados.get("data_saida") and dados.get("questao"))
    return dados, ok


_FORMS = {
    "🏢  Diagnóstico Tributário Empresarial": _form_empresarial,
    "👤  Check-up Fiscal — Pessoa Física":    _form_pf,
    "🌾  Produtor Rural / Agronegócio":        _form_rural,
    "🏛️  Holding Familiar e Sucessória":       _form_holding,
    "📊  Planejamento Tributário Estratégico": _form_estrategico,
    "⚖️  Contencioso Fiscal e Defesas":        _form_contencioso,
}


def render_formulario(tipo):
    return _FORMS.get(tipo, _form_empresarial)()


# ── Formatação para o Claude ──────────────────────────────────────────────────

def formatar_descricao(dados, tipo, dre_texto=None, previsao=None):
    t = tipo
    if t == "🏢  Diagnóstico Tributário Empresarial":
        desc = (
            f"Tipo de Diagnóstico: Diagnóstico Tributário Empresarial\n"
            f"Setor/Segmento: {dados.get('setor','')}\n"
            f"Regime Tributário Atual: {dados.get('regime','')}\n"
            f"Faturamento Anual Aproximado: {dados.get('faturamento','')}\n"
            f"Descrição das Atividades: {dados.get('atividades','')}\n"
            f"Dúvida / Objetivo Específico: {dados.get('questao','')}"
        )
    elif t == "👤  Check-up Fiscal — Pessoa Física":
        desc = (
            f"Tipo de Diagnóstico: Check-up Fiscal Pessoa Física\n"
            f"Profissão / Ocupação: {dados.get('profissao','')}\n"
            f"Renda Bruta Anual Total: {dados.get('renda_anual','')}\n"
            f"Estado Civil: {dados.get('estado_civil','')}\n"
            f"Fontes de Renda: {dados.get('fontes_renda','')}\n"
            f"Possui Imóveis: {dados.get('tem_imoveis','')}\n"
            f"Investimentos: {dados.get('investimentos','')}\n"
            f"Dúvida / Objetivo: {dados.get('questao','')}"
        )
    elif t == "🌾  Produtor Rural / Agronegócio":
        desc = (
            f"Tipo de Diagnóstico: Produtor Rural / Agronegócio\n"
            f"Tipo de Atividade Rural: {dados.get('tipo_atividade','')}\n"
            f"Perfil: {dados.get('perfil','')}\n"
            f"Faturamento Rural Anual: {dados.get('faturamento','')}\n"
            f"Descrição das Atividades: {dados.get('atividades','')}\n"
            f"Exporta: {dados.get('exporta','')}\n"
            f"Trabalhadores Rurais: {dados.get('funcionarios_rurais','')}\n"
            f"Dúvida / Objetivo: {dados.get('questao','')}"
        )
    elif t == "🏛️  Holding Familiar e Sucessória":
        desc = (
            f"Tipo de Diagnóstico: Holding Familiar e Sucessória\n"
            f"Tipo de Holding: {dados.get('tipo_holding','')}\n"
            f"Patrimônio Total Estimado: {dados.get('patrimonio','')}\n"
            f"Estado(s) dos Bens: {dados.get('estado_bens','')}\n"
            f"Número de Herdeiros/Sócios: {dados.get('num_herdeiros','')}\n"
            f"Descrição do Patrimônio e Objetivos: {dados.get('descricao','')}\n"
            f"Dúvida / Objetivo: {dados.get('questao','')}"
        )
    elif t == "📊  Planejamento Tributário Estratégico":
        desc = (
            f"Tipo de Diagnóstico: Planejamento Tributário Estratégico\n"
            f"Setor/Segmento: {dados.get('setor','')}\n"
            f"Regime Tributário Atual: {dados.get('regime','')}\n"
            f"Faturamento Atual: {dados.get('faturamento','')}\n"
            f"Margem de Lucro Real Estimada: {dados.get('margem_lucro','')}\n"
            f"Número de Funcionários: {dados.get('num_funcionarios','')}\n"
            f"Folha de Pagamento Mensal: {dados.get('folha_mensal','')}\n"
            f"Objetivo do Planejamento: {dados.get('objetivo','')}\n"
            f"Decisão a Tomar / Dúvida: {dados.get('questao','')}"
        )
    elif t == "⚖️  Contencioso Fiscal e Defesas":
        desc = (
            f"Tipo de Diagnóstico: Contencioso Fiscal e Defesas\n"
            f"Setor/Segmento: {dados.get('setor','')}\n"
            f"Regime Tributário: {dados.get('regime','')}\n"
            f"Tributo em Discussão: {dados.get('tributo','')}\n"
            f"Esfera Processual: {dados.get('esfera','')}\n"
            f"Valor Envolvido: {dados.get('valor_envolvido','')}\n"
            f"Descrição do Caso: {dados.get('descricao','')}\n"
            f"Objetivo / Decisão a Tomar: {dados.get('questao','')}"
        )
    else:
        desc = str(dados)

    if dre_texto:
        desc += f"\n\n--- DADOS FINANCEIROS (DRE) ---\n{dre_texto[:8000]}"
    if previsao:
        desc += f"\n\n--- PREVISÃO DE FATURAMENTO E PROJEÇÕES ---\n{previsao}"

    return desc


def formatar_descricao_transicao(dados):
    return (
        f"Tipo de Análise: Saída Fiscal Brasil para EUA — Tributação Bilateral\n"
        f"País Atual de Residência: {dados.get('pais_residencia','')}\n"
        f"Data de Saída do Brasil: {dados.get('data_saida','')}\n"
        f"Tipo de Saída: {dados.get('tipo_saida','')}\n"
        f"Comunicação de Saída Definitiva (CSD): {dados.get('csd','')}\n"
        f"Declaração de Saída Definitiva (DSD): {dados.get('dsd','')}\n"
        f"Retornos ao Brasil após a saída: {dados.get('retornos','')}\n"
        f"Status Migratório nos EUA: {dados.get('status_eua','')}\n"
        f"Empresa no Brasil: {dados.get('empresa_brasil','')}\n"
        f"Rendimentos no Exterior: {dados.get('rendimentos_exterior','')}\n"
        f"Entidade / LLC no Exterior: {dados.get('entidade_exterior','')}\n"
        f"Total de Ativos no Exterior (USD): {dados.get('ativos_exterior_usd','')}\n"
        f"Bens e Vínculos Mantidos no Brasil: {dados.get('bens_brasil','')}\n"
        f"Rendimentos de Fonte Brasileira: {dados.get('renda_brasil','')}\n"
        f"Dúvida / Objetivo Principal: {dados.get('questao','')}"
    )


# ── API ───────────────────────────────────────────────────────────────────────

def analisar(dados, tipo, dre_texto=None, previsao=None, modulo="brasil"):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    system = build_system_prompt(tipo, modulo)
    if modulo == "transicao":
        descricao = formatar_descricao_transicao(dados)
        max_tok = 4000
    else:
        descricao = formatar_descricao(dados, tipo, dre_texto, previsao)
        max_tok = 3500
    resposta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tok,
        system=system,
        messages=[{"role": "user", "content": descricao}]
    )
    return resposta.content[0].text


# ── Risco e PDF ───────────────────────────────────────────────────────────────

def calcular_nivel_risco(texto):
    vermelhos = texto.count("🔴")
    amarelos  = texto.count("🟡")
    if vermelhos >= 2:   return "ALTO",       vermelhos, amarelos
    if vermelhos == 1 or amarelos >= 3: return "MÉDIO-ALTO", vermelhos, amarelos
    if amarelos >= 1:    return "MÉDIO",      vermelhos, amarelos
    return "BAIXO", vermelhos, amarelos


def badge_risco(nivel, vermelhos, amarelos):
    paleta = {
        "ALTO":       ("#2a0a0a", "#8b1c1c", "#f05252", "#fca5a5"),
        "MÉDIO-ALTO": ("#1c1203", "#7c5010", "#e3a008", "#fcd34d"),
        "MÉDIO":      ("#1c1203", "#7c5010", "#d4ac0d", "#fde68a"),
        "BAIXO":      ("#0a1c0d", "#1a5c2a", "#31c45d", "#86efac"),
    }
    emojis = {"ALTO": "🔴", "MÉDIO-ALTO": "🟠", "MÉDIO": "🟡", "BAIXO": "🟢"}
    bg, border, cor_nivel, cor_label = paleta.get(nivel, paleta["MÉDIO"])
    emoji = emojis.get(nivel, "🟡")
    contagem = f"{vermelhos} risco(s) alto(s) &nbsp;·&nbsp; {amarelos} alerta(s) médio(s)"
    return (
        f'<div style="background:{bg}; border:1.5px solid {border}; border-radius:10px;'
        f' padding:1rem 1.5rem; margin:0.5rem 0 1.5rem; display:flex; align-items:center; gap:1.2rem;">'
        f'<span style="font-size:2.2rem; line-height:1;">{emoji}</span>'
        f'<div><div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.12em;'
        f' font-weight:700; color:{cor_label}; margin-bottom:0.15rem;">Nível de Risco Fiscal Identificado</div>'
        f'<div style="font-size:1.45rem; font-weight:800; color:{cor_nivel}; line-height:1.1;">{nivel}</div></div>'
        f'<div style="margin-left:auto; text-align:right; font-size:0.75rem; color:{border}; opacity:0.9;">{contagem}</div>'
        f'</div>'
    )


def _limpar_para_pdf(texto):
    subst = {
        "🔴": "[ALTO]", "🟡": "[MEDIO]", "🟢": "[BAIXO]", "🟠": "[MEDIO-ALTO]",
        "⚡": "[!]", "📅": "", "🔭": "", "✓": "[OK]", "━": "-",
        "—": "-", "–": "-", "'": "'", "‘": "'", "’": "'",
        "“": '"', "”": '"', "→": "->", "🇧🇷": "[BR]", "🇺🇸": "[EUA]",
        "⚪": "[?]",
    }
    for orig, repl in subst.items():
        texto = texto.replace(orig, repl)
    return texto.encode("latin-1", errors="replace").decode("latin-1")


def _mc(pdf, h, texto):
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, texto)


def get_pdf_meta(dados, tipo):
    t = tipo
    if t == "🏢  Diagnóstico Tributário Empresarial":
        return dados.get("setor",""), dados.get("regime",""), dados.get("faturamento","")
    if t == "👤  Check-up Fiscal — Pessoa Física":
        return dados.get("profissao",""), dados.get("estado_civil",""), dados.get("renda_anual","")
    if t == "🌾  Produtor Rural / Agronegócio":
        return dados.get("tipo_atividade",""), dados.get("perfil",""), dados.get("faturamento","")
    if t == "🏛️  Holding Familiar e Sucessória":
        return dados.get("tipo_holding",""), dados.get("estado_bens",""), dados.get("patrimonio","")
    if t == "📊  Planejamento Tributário Estratégico":
        return dados.get("setor",""), dados.get("regime",""), dados.get("faturamento","")
    if t == "⚖️  Contencioso Fiscal e Defesas":
        return dados.get("tributo",""), dados.get("esfera",""), dados.get("valor_envolvido","")
    if t == "transicao":
        return dados.get("pais_residencia",""), dados.get("tipo_saida",""), dados.get("data_saida","")
    return "", "", ""


def gerar_pdf(resultado, dados, tipo_diagnostico):
    tipo_limpo = _limpar_para_pdf(re.sub(r"[^\w\s\-/.,>]", " ", tipo_diagnostico).strip())
    meta1, meta2, meta3 = [_limpar_para_pdf(s) for s in get_pdf_meta(dados, tipo_diagnostico)]
    texto = _limpar_para_pdf(resultado)

    if tipo_diagnostico == "transicao":
        subtitulo = "Analista Tributario Assistido por IA  |  Analise Bilateral Brasil-EUA"
        tipo_limpo = "Saida Fiscal Brasil -> EUA"
    else:
        subtitulo = "Analista Tributario Assistido por IA  |  Prototipo 0.1"

    pdf = FPDF()
    pdf.set_margins(left=15, top=15, right=15)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    lx, rx = pdf.l_margin, pdf.w - pdf.r_margin

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(200, 151, 58)
    pdf.set_x(lx); pdf.cell(pdf.epw, 10, "MAGUS Fiscal", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 140)
    pdf.set_x(lx); pdf.cell(pdf.epw, 6, subtitulo, ln=True)

    pdf.ln(3)
    pdf.set_draw_color(50, 50, 70)
    pdf.line(lx, pdf.get_y(), rx, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(140, 140, 165)
    _mc(pdf, 5, f"Tipo: {tipo_limpo}")
    _mc(pdf, 5, f"{meta1}  |  {meta2}  |  {meta3}")
    pdf.set_x(lx); pdf.cell(pdf.epw, 5, f"Data: {datetime.now().strftime('%d/%m/%Y  %H:%M')}", ln=True)

    pdf.ln(3)
    pdf.line(lx, pdf.get_y(), rx, pdf.get_y())
    pdf.ln(6)

    pdf.set_text_color(30, 30, 40)
    for linha in texto.split("\n"):
        ls = linha.strip()
        if ls.startswith("# "):
            pdf.set_font("Helvetica", "B", 13); pdf.set_text_color(160, 100, 20)
            _mc(pdf, 7, ls.lstrip("# ").strip())
            pdf.set_text_color(30, 30, 40); pdf.ln(1)
        elif ls.startswith("## "):
            pdf.set_font("Helvetica", "B", 11); pdf.set_text_color(130, 80, 15)
            _mc(pdf, 6, ls.lstrip("# ").strip())
            pdf.set_text_color(30, 30, 40); pdf.ln(1)
        elif ls.startswith("---"):
            pdf.ln(2); pdf.set_draw_color(190, 190, 210)
            pdf.line(lx, pdf.get_y(), rx, pdf.get_y()); pdf.ln(4)
        elif ls == "":
            pdf.ln(3)
        else:
            limpa = re.sub(r"\*\*(.*?)\*\*", r"\1", linha)
            pdf.set_font("Helvetica", "", 10); pdf.set_text_color(30, 30, 40)
            _mc(pdf, 6, limpa)

    pdf.ln(8)
    pdf.set_draw_color(50, 50, 70)
    pdf.line(lx, pdf.get_y(), rx, pdf.get_y()); pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8); pdf.set_text_color(120, 120, 140)
    pdf.set_x(lx)
    pdf.cell(pdf.epw, 5, "MAGUS Fiscal - Prototipo 0.1  |  Use apenas dados ficticios ou anonimizados", align="C")

    return bytes(pdf.output())


# ── Extração de arquivos ──────────────────────────────────────────────────────

def extrair_texto_pdf(arq):
    with pdfplumber.open(arq) as pdf:
        return "".join(p.extract_text() or "" for p in pdf.pages).strip()

def extrair_texto_excel(arq):
    return pd.read_excel(arq, header=None).to_string(index=False)

def extrair_texto_csv(arq):
    try:
        return pd.read_csv(arq, on_bad_lines="skip").to_string(index=False)
    except Exception:
        arq.seek(0)
        return arq.read().decode("utf-8", errors="ignore")

def extrair_conteudo_arquivo(arq):
    n = arq.name.lower()
    if n.endswith(".pdf"):   return extrair_texto_pdf(arq)
    if n.endswith((".xlsx", ".xls")): return extrair_texto_excel(arq)
    if n.endswith(".csv"):   return extrair_texto_csv(arq)
    return None


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
<style>
    .stApp {
        background-color: #0a0d14;
        background-image:
            linear-gradient(rgba(200,151,58,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(200,151,58,0.04) 1px, transparent 1px),
            radial-gradient(ellipse at 20% 50%, rgba(200,151,58,0.06) 0%, transparent 60%),
            radial-gradient(ellipse at 80% 20%, rgba(30,60,120,0.15) 0%, transparent 50%);
        background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%;
    }
    .section-title { color:#c8973a; font-size:1rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem; }
    .stTextInput label, .stSelectbox label, .stTextArea label, .stFileUploader label { color:#c8c8c8 !important; font-size:0.9rem !important; font-weight:500 !important; }
    .stTextInput input, .stTextArea textarea, .stNumberInput input { background-color:#141824 !important; border:1px solid #2d3348 !important; color:#e8e8e8 !important; border-radius:6px !important; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color:#c8973a !important; box-shadow:0 0 0 1px #c8973a !important; }
    .stSelectbox > div > div { background-color:#141824 !important; border:1px solid #2d3348 !important; color:#e8e8e8 !important; border-radius:6px !important; }
    .stFileUploader > div { background-color:#141824 !important; border:1px dashed #2d3348 !important; border-radius:6px !important; }
    .stFileUploader > div:hover { border-color:#c8973a !important; }
    .stExpander { background-color:#141824 !important; border:1px solid #2d3348 !important; border-radius:6px !important; }
    .stExpander summary { color:#c8973a !important; font-weight:600 !important; }
    .stButton > button[kind="primary"] { background-color:#c8973a !important; color:#0a0d14 !important; font-weight:700 !important; font-size:1rem !important; border:none !important; padding:0.6rem 2rem !important; border-radius:6px !important; width:100%; letter-spacing:0.03em; }
    .stButton > button[kind="primary"]:hover { background-color:#e0aa4a !important; }
    .stButton > button[kind="secondary"] { background-color:#141824 !important; color:#8a8f9e !important; border:1px solid #2d3348 !important; font-weight:600 !important; font-size:0.9rem !important; border-radius:6px !important; width:100%; }
    .stButton > button[kind="secondary"]:hover { border-color:#c8973a !important; color:#c8973a !important; background-color:#141824 !important; }
    .stButton > button:disabled { opacity:0.4 !important; }
    .resultado-titulo { color:#c8973a; font-size:1rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:1rem; padding-bottom:0.5rem; border-bottom:1px solid #2d3348; }
    hr { border-color:#2d3348 !important; }
    .stAlert { background-color:#141824 !important; border:1px solid #2d3348 !important; border-radius:6px !important; }
    .magus-footer { color:#3d4357; font-size:0.75rem; text-align:center; margin-top:2rem; padding-top:1rem; border-top:1px solid #1a1f2e; }
    .arquivo-ok { background-color:#0d1f12; border:1px solid #2a5c35; border-radius:6px; padding:0.5rem 0.8rem; color:#5cb87a; font-size:0.85rem; margin-top:0.3rem; }
    .tipo-desc { color:#7a8099; font-size:0.82rem; margin-top:0.2rem; font-style:italic; }
    .banner-transicao { background:#0a1420; border:1px solid #1a3a5c; border-radius:8px; padding:0.8rem 1.2rem; margin-bottom:1rem; }
    .banner-transicao-titulo { color:#4a9eff; font-size:0.85rem; font-weight:600; margin-bottom:0.3rem; }
    .banner-transicao-texto { color:#7a90a8; font-size:0.82rem; }
</style>
"""

# ── Session state ─────────────────────────────────────────────────────────────

for k, v in [("resultado", None), ("analise_dados", {}), ("analise_tipo", ""), ("modulo", "brasil")]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Layout ────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="MAGUS Fiscal", page_icon="assets/favicon.png", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div style='display:flex; align-items:center; gap:1.2rem; padding:0.5rem 0 1rem 0;'>
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="68" height="68">
    <g transform="translate(256,256)">
      <path d="M -130,0 C -130,-60 -38,-60 0,0 C 38,60 130,60 130,0 C 130,-60 38,-60 0,0 C -38,60 -130,60 -130,0"
        fill="none" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"/>
      <line x1="160" y1="-22" x2="160" y2="22" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"/>
      <line x1="188" y1="-12" x2="188" y2="12" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"/>
    </g>
  </svg>
  <div>
    <div style='color:#c8973a; font-size:1.8rem; font-weight:700; letter-spacing:0.05em; line-height:1.1;'>MAGUS Fiscal</div>
    <div style='color:#8a8f9e; font-size:0.9rem; margin-top:0.25rem;'>Analista Tributário Assistido por IA · Protótipo 0.1</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Seletor de módulo ──────────────────────────────────────────────────────────

mod_c1, mod_c2, mod_c3 = st.columns([1.5, 2.2, 4])
with mod_c1:
    btn_brasil = st.button(
        "🇧🇷  Módulo Brasil",
        key="btn_mod_brasil",
        type="primary" if st.session_state.modulo == "brasil" else "secondary",
        use_container_width=True
    )
with mod_c2:
    btn_transicao = st.button(
        "🇧🇷🇺🇸  Transição Brasil → EUA",
        key="btn_mod_transicao",
        type="primary" if st.session_state.modulo == "transicao" else "secondary",
        use_container_width=True
    )

if btn_brasil and st.session_state.modulo != "brasil":
    st.session_state.modulo = "brasil"
    st.session_state.resultado = None
    st.rerun()
if btn_transicao and st.session_state.modulo != "transicao":
    st.session_state.modulo = "transicao"
    st.session_state.resultado = None
    st.rerun()

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO BRASIL
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.modulo == "brasil":

    st.markdown('<div class="section-title">Tipo de Diagnóstico</div>', unsafe_allow_html=True)
    tipo_diagnostico = st.selectbox("Tipo", options=list(TIPO_DESCRICOES.keys()), label_visibility="collapsed")
    st.markdown(f'<div class="tipo-desc">{TIPO_DESCRICOES.get(tipo_diagnostico,"")}</div>', unsafe_allow_html=True)
    st.markdown("")
    st.divider()

    st.markdown('<div class="section-title">Dados para Análise</div>', unsafe_allow_html=True)
    st.markdown("")

    dados, campos_ok = render_formulario(tipo_diagnostico)

    st.divider()

    cfg = TIPO_CONFIG.get(tipo_diagnostico, {"dre": False, "avancado": False})

    dre_texto = None

    if cfg["dre"]:
        st.markdown('<div class="section-title">Dados Financeiros — DRE (opcional)</div>', unsafe_allow_html=True)
        st.caption("Forneça os dados financeiros para enriquecer a análise.")

        aba_upload, aba_form = st.tabs(["📎  Carregar arquivo (PDF, Excel, CSV)", "📝  Preencher formulário manualmente"])

        with aba_upload:
            st.markdown("")
            arq = st.file_uploader("DRE", type=["pdf","xlsx","xls","csv"], label_visibility="collapsed")
            if arq:
                try:
                    dre_texto = extrair_conteudo_arquivo(arq)
                    if dre_texto:
                        st.markdown(f'<div class="arquivo-ok">✓ Arquivo carregado: <strong>{arq.name}</strong></div>', unsafe_allow_html=True)
                    else:
                        st.warning("Não foi possível extrair texto deste arquivo.")
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")

        with aba_form:
            st.markdown("")
            st.markdown("**Preencha o que souber. Deixe em branco o restante.**")
            fc1, fc2 = st.columns(2)
            with fc1:
                st.markdown("**Receitas**")
                dre_rb  = st.text_input("Receita Bruta Total", placeholder="Ex: 6.200.000", key="dre_rb")
                dre_ded = st.text_input("Deduções (ISS, PIS, COFINS)", placeholder="Ex: 412.300", key="dre_ded")
                dre_rl  = st.text_input("Receita Líquida", placeholder="Ex: 5.787.700", key="dre_rl")
                st.markdown("**Custos**")
                dre_mat = st.text_input("Materiais / Insumos", placeholder="Ex: 2.232.000", key="dre_mat")
                dre_mo  = st.text_input("Mão de obra direta", placeholder="Ex: 1.116.000", key="dre_mo")
                dre_ter = st.text_input("Subcontratados / Terceiros", placeholder="Ex: 558.000", key="dre_ter")
                dre_ct  = st.text_input("Total de Custos", placeholder="Ex: 4.216.000", key="dre_ct")
                dre_lb  = st.text_input("Lucro Bruto", placeholder="Ex: 1.571.700", key="dre_lb")
            with fc2:
                st.markdown("**Despesas Operacionais**")
                dre_adm = st.text_input("Despesas Administrativas", placeholder="Ex: 420.000", key="dre_adm")
                dre_sal = st.text_input("Salários e encargos administrativo", placeholder="Ex: 312.000", key="dre_sal")
                dre_com = st.text_input("Despesas Comerciais", placeholder="Ex: 124.000", key="dre_com")
                dre_fin = st.text_input("Despesas Financeiras (juros, IOF)", placeholder="Ex: 248.000", key="dre_fin")
                dre_dep = st.text_input("Depreciação", placeholder="Ex: 186.000", key="dre_dep")
                st.markdown("**Resultado e Pessoal**")
                dre_res = st.text_input("Resultado antes do IR/CSLL", placeholder="Ex: 281.700", key="dre_res")
                dre_ir  = st.text_input("IR e CSLL pagos", placeholder="Ex: 123.008", key="dre_ir")
                dre_ll  = st.text_input("Lucro Líquido", placeholder="Ex: 158.692", key="dre_ll")
                dre_func = st.text_input("Funcionários CLT", placeholder="Ex: 42", key="dre_func")
                dre_folha= st.text_input("Folha mensal", placeholder="Ex: 186.000", key="dre_folha")

            campos_form = [dre_rb, dre_rl, dre_lb, dre_ll, dre_mat, dre_mo, dre_res]
            if any(campos_form):
                linhas = ["--- DADOS FINANCEIROS (DRE — Formulário) ---"]
                for label, val in [
                    ("Receita Bruta", dre_rb), ("Deduções", dre_ded), ("Receita Líquida", dre_rl),
                    ("Materiais/Insumos", dre_mat), ("Mão de obra direta", dre_mo),
                    ("Subcontratados", dre_ter), ("Total de Custos", dre_ct), ("Lucro Bruto", dre_lb),
                    ("Desp. Administrativas", dre_adm), ("Salários Adm.", dre_sal),
                    ("Desp. Comerciais", dre_com), ("Desp. Financeiras", dre_fin),
                    ("Depreciação", dre_dep), ("Result. antes IR/CSLL", dre_res),
                    ("IR e CSLL pagos", dre_ir), ("Lucro Líquido", dre_ll),
                    ("Funcionários CLT", dre_func), ("Folha mensal", dre_folha),
                ]:
                    if val: linhas.append(f"{label}: R$ {val}" if label != "Funcionários CLT" else f"Funcionários CLT: {val}")
                dre_texto = "\n".join(linhas)
                st.markdown('<div class="arquivo-ok">✓ Formulário preenchido — dados prontos para análise.</div>', unsafe_allow_html=True)

        st.divider()

    previsao_texto = None

    if cfg["avancado"]:
        with st.expander("Opções Avançadas — Previsão de Faturamento e Simulação de Regime"):
            st.caption("Informe projeções para que o MAGUS compare regimes e simule cenários.")
            ca, cb = st.columns(2)
            with ca:
                fat1 = st.text_input("Faturamento Projetado (próximo ano)", placeholder="Ex: R$ 4 milhões")
                fat2 = st.text_input("Faturamento Projetado (em 2 anos)", placeholder="Ex: R$ 8 milhões")
            with cb:
                nfunc = st.text_input("Número de Funcionários", placeholder="Ex: 12")
                folha = st.text_input("Folha de Pagamento Mensal", placeholder="Ex: R$ 80 mil")
            obs = st.text_area("Observações adicionais", placeholder="Ex: Pretendemos abrir filial em outro estado...", height=70)
            if fat1 or fat2:
                partes = []
                if fat1:  partes.append(f"Faturamento projetado próximo ano: {fat1}")
                if fat2:  partes.append(f"Faturamento projetado 2 anos: {fat2}")
                if nfunc: partes.append(f"Número de funcionários: {nfunc}")
                if folha: partes.append(f"Folha mensal: {folha}")
                if obs:   partes.append(f"Observações: {obs}")
                previsao_texto = "\n".join(partes)
        st.divider()

    if not campos_ok:
        st.info("Preencha os campos obrigatórios para iniciar a análise.")

    btn = st.button("Analisar", type="primary", disabled=not campos_ok)

    if btn:
        with st.spinner("Analisando... Isso pode levar alguns segundos."):
            try:
                resultado = analisar(dados, tipo_diagnostico, dre_texto, previsao_texto, modulo="brasil")
                st.session_state.resultado    = resultado
                st.session_state.analise_dados = dados
                st.session_state.analise_tipo  = tipo_diagnostico
            except Exception as e:
                st.error(f"Erro ao conectar com o motor de IA: {e}")

    if st.session_state.resultado:
        st.divider()
        nivel, vm, am = calcular_nivel_risco(st.session_state.resultado)
        st.markdown(badge_risco(nivel, vm, am), unsafe_allow_html=True)
        st.markdown('<div class="resultado-titulo">Análise MAGUS Fiscal</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.resultado)
        st.divider()

        c_dl, c_lim = st.columns([3, 1])
        with c_dl:
            pdf_bytes = gerar_pdf(st.session_state.resultado, st.session_state.analise_dados, st.session_state.analise_tipo)
            nome = f"MAGUS_Fiscal_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("📄  Baixar Relatório em PDF", data=pdf_bytes, file_name=nome, mime="application/pdf")
        with c_lim:
            if st.button("✕  Limpar análise"):
                st.session_state.resultado = None
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MÓDULO TRANSIÇÃO BRASIL → EUA
# ══════════════════════════════════════════════════════════════════════════════

else:

    st.markdown("""
    <div class="banner-transicao">
      <div class="banner-transicao-titulo">🇧🇷🇺🇸  MÓDULO — SAÍDA FISCAL BRASIL → EUA</div>
      <div class="banner-transicao-texto">
        Triagem fiscal para brasileiros residindo ou em transição para os Estados Unidos.
        Analisa residência fiscal, carnê-leão, LLC sob Lei 14.754/2023, CBE/DCBE, empresa brasileira no Simples/MEI
        e gera memo em inglês para o contador americano.
        Os resultados são estimativas educacionais — casos complexos exigem revisão profissional.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Dados para Análise</div>', unsafe_allow_html=True)
    st.markdown("")

    dados_t, campos_ok_t = _form_transicao()

    st.divider()

    if not campos_ok_t:
        st.info("Preencha pelo menos: País de residência, Data de saída do Brasil e Dúvida/Objetivo.")

    btn_t = st.button("Analisar", type="primary", disabled=not campos_ok_t, key="btn_analisar_transicao")

    if btn_t:
        with st.spinner("Analisando situação fiscal bilateral... Isso pode levar alguns segundos."):
            try:
                resultado_t = analisar(dados_t, "transicao", modulo="transicao")
                st.session_state.resultado    = resultado_t
                st.session_state.analise_dados = dados_t
                st.session_state.analise_tipo  = "transicao"
            except Exception as e:
                st.error(f"Erro ao conectar com o motor de IA: {e}")

    if st.session_state.resultado and st.session_state.analise_tipo == "transicao":
        st.divider()
        nivel, vm, am = calcular_nivel_risco(st.session_state.resultado)
        st.markdown(badge_risco(nivel, vm, am), unsafe_allow_html=True)
        st.markdown('<div class="resultado-titulo">Análise MAGUS Fiscal — Saída Fiscal Brasil → EUA</div>', unsafe_allow_html=True)
        st.markdown(st.session_state.resultado)
        st.divider()

        c_dl, c_lim = st.columns([3, 1])
        with c_dl:
            pdf_bytes = gerar_pdf(st.session_state.resultado, st.session_state.analise_dados, "transicao")
            nome = f"MAGUS_Saida_Fiscal_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("📄  Baixar Relatório em PDF", data=pdf_bytes, file_name=nome, mime="application/pdf")
        with c_lim:
            if st.button("✕  Limpar análise", key="limpar_transicao"):
                st.session_state.resultado = None
                st.rerun()

st.divider()
st.markdown('<div class="magus-footer">MAGUS Fiscal — Protótipo 0.1 &nbsp;|&nbsp; Use apenas dados fictícios ou anonimizados</div>', unsafe_allow_html=True)
