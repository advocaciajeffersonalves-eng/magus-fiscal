# Roteiro de Perguntas — Contrato de Vesting

> Questionário guiado (determinístico, sem custo de IA). Cada resposta preenche um
> campo do contrato ou ativa/desativa um módulo. A IA só entra no acabamento final.

## BLOCO 1 — Quem e o quê (identificação)

1. **Razão social da Sociedade** → campo `[SOCIEDADE]`
2. **CNPJ, sede (cidade/UF) e NIRE/Junta** → campos de qualificação
3. **Sócios outorgantes** (nome + qualificação de cada) → `[OUTORGANTES]`
4. **Quem vai receber o vesting** (nome, CPF, função) → `[OUTORGADO]`
5. **Perfil do beneficiário:**
   - ( ) Sócio/colaborador que trabalha na empresa  → usa **cliff + metas**
   - ( ) Consultor ou investidor estratégico externo → habilita **M1 Vesting imediato**
6. **Capital social** (valor total, nº de quotas, valor nominal) → considerandos

## BLOCO 2 — Estrutura do vesting

7. **Percentual de participação oferecido** (ex: 5%) → `[PERCENTUAL]`
8. **Vai ter carência (cliff)?** Se sim, quanto? (ex: 12 meses) → `[CLIFF]`
9. **Prazo total do vesting** (ex: 48 meses) → `[PRAZO_VESTING]`
10. **Como o beneficiário "ganha" a participação ao longo do tempo:**
    - ( ) Por tempo de permanência (ex: parcelas mensais/anuais)
    - ( ) Por metas de performance
    - ( ) Os dois combinados
    → monta o **Anexo de Métricas/Cronograma**
11. **Preço para exercer a opção** (critério de valuation — ex: múltiplo de EBITDA + teto) → `[PRECO_OPCAO]`

## BLOCO 3 — Saída e recompra

12. **Como calcular a recompra em cada cenário:**
    - Dispensa sem justa causa / rescisão pela empresa → `[RECOMPRA_SEM_JC]`
    - Saída voluntária (múltiplo de EBITDA + teto) → `[RECOMPRA_VOLUNTARIA]`
    - Justa causa (devolve valor pago + CDI) → padrão
13. **Parcelamento da recompra** (ex: até 24x) → `[PARCELAS_RECOMPRA]`

## BLOCO 4 — Proteções (módulos liga/desliga)

14. **A empresa pretende captar investimento / fazer rodadas?**
    Sim → ativa **M2 Anti-diluição** (Broad-Based Weighted Average)
15. **Proteger o beneficiário se a empresa for vendida?**
    Sim → ativa **M3 Aceleração** (full acceleration na mudança de controle)
16. **Dar direito de vender junto se os sócios majoritários venderem?**
    Sim → ativa **M4 Tag Along**
17. **O beneficiário recebe dividendos/lucros desde já?**
    Sim → ativa **M5 Direitos econômicos + acesso à informação + blindagem patrimonial**
18. **Usar critérios objetivos de "Causa" e "Good Reason" para rescisão?**
    Sim → ativa **M6**

## BLOCO 5 — Restrições e proteção da empresa

19. **Não-competição:** período após a saída (ex: 6 anos) + multa → `[NAO_COMPETE]`
20. **Confidencialidade:** prazo após o fim (ex: 5 anos) + multa → `[CONFIDENCIALIDADE]`
21. **O beneficiário cria conteúdo/produto/PI para a empresa?**
    Sim → mantém **Cláusula de Cessão de Propriedade Intelectual**

## BLOCO 6 — Foro e fechamento

22. **Resolução de conflitos:**
    - ( ) Arbitragem (CAMARB) — padrão nacional
    - ( ) Foro judicial (qual comarca)
    - ( ) Internacional (lei/foro estrangeiro) → **Variante internacional**
23. **Cidade e data de assinatura** + **2 testemunhas** → fechamento

---

### Lógica de economia
- Perguntas = formulário guiado, **custo zero de IA**.
- Campos preenchidos por código.
- IA (Haiku) só no acabamento: encaixar redações dos módulos ativados e revisar coesão.
