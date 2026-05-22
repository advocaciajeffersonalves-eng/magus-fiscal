# CLAUDE.md — Briefing do Projeto MAGUS Fiscal

> **Este arquivo é lido automaticamente pelo Claude Code ao iniciar nesta pasta.**
> Ele transfere o contexto da sessão de planejamento (Cowork) para a sessão de construção (Claude Code).
> Mantenha-o atualizado conforme o projeto evolui.

---

## Identidade do projeto

**Empresa:** MAGUS.IA (razão social: MAGUS IA TECNOLOGIA LTDA, em constituição). Holding controladora: ABM Holding de Participações Ltda.

**Produto sendo construído:** MAGUS Fiscal — plataforma de IA vertical para advogados tributaristas e contadores brasileiros.

**O que estamos construindo AGORA:** o **Protótipo 0** — codinome "Analista Tributário Assistido". Primeira versão funcional, que prova o conceito.

**Tese central:** IA vertical, não horizontal. O valor não está em treinar um modelo — está na camada de especialização tributária construída em cima de um modelo existente (Claude via API).

---

## Quem é o usuário — LEIA COM ATENÇÃO

**Nome:** Jefferson Alves Batista.

**Perfil:** Advogado tributarista (OAB-GO 39.292), empresário, 43 anos. **NÃO é programador.** Não tem conhecimento avançado em Python ou desenvolvimento de software. Está aprendendo a construir conforme avança.

**O que ele DOMINA:** direito tributário brasileiro, engenharia tributária, a dor real do profissional do setor, a Reforma Tributária. Essa expertise é o ativo central do produto.

**O que ele NÃO domina (ainda):** programação, terminal, arquitetura de software, ferramentas de desenvolvimento. Está construindo esse conhecimento agora.

### Como trabalhar com o Jefferson — regras

1. **Explique tudo.** Cada termo técnico, cada comando, cada conceito. Nunca assuma conhecimento prévio de programação. Se usar uma palavra técnica, explique-a na hora.
2. **Ensine enquanto constrói.** O objetivo dele não é só ter o produto — é entender o que está sendo construído. Comente o "porquê" de cada decisão.
3. **Vá em ritmo paciente.** Passos pequenos, confirmação a cada etapa. Não despeje 20 comandos de uma vez.
4. **Antes de rodar comandos que modificam o sistema**, explique o que o comando faz e o que ele vai ver acontecer.
5. **Erros são normais e esperados.** Quando algo der errado, trate como aprendizado, não como falha. Diagnostique com calma.
6. **Respostas diretas e objetivas**, sem rodeios. Use exemplos práticos. Ele prefere prosa a listas longas quando a explicação em prosa funciona.
7. **Discorde quando ele estiver tecnicamente errado.** Ele valoriza honestidade técnica acima de concordância.
8. **O foco é construção de riqueza.** Tudo que for feito deve cooperar com o objetivo de transformar a MAGUS.IA num negócio real e lucrativo.

---

## O que é o Protótipo 0

Um programa que roda no Mac Mini M4 do Jefferson, abre no navegador (via Streamlit), e faz:

1. **Entrada:** Jefferson descreve a situação tributária de uma empresa — setor, regime tributário, faturamento aproximado, atividades, dúvida/objetivo específico. (Entrada em texto estruturado, NÃO processamento de arquivos SPED/ECF reais nesta versão.)
2. **Processamento:** chamada à API da Anthropic (Claude) com um **system prompt especializado** em engenharia tributária brasileira.
3. **Saída:** análise estruturada — créditos tributários a investigar, riscos fiscais, oportunidades de planejamento, esboço de parecer preliminar, próximas perguntas e documentos necessários.

### Arquitetura do Protótipo 0

- **Linguagem:** Python
- **Interface:** Streamlit (roda local, abre no navegador)
- **Motor de IA:** Claude via API da Anthropic. Modelo sugerido para começar: `claude-sonnet-4-6` (bom equilíbrio custo/capacidade); usar `claude-opus-4-6` para casos que exijam raciocínio mais profundo.
- **Bibliotecas:** `anthropic`, `streamlit`, `python-dotenv`
- **Chave de API:** guardada em arquivo `.env` (NUNCA hardcoded, NUNCA versionada)

### As 3 peças do Protótipo 0

1. **Interface (Streamlit)** — onde Jefferson digita e lê resultados. Encanamento padronizado.
2. **Camada de especialização (system prompt)** — a peça mais importante. É um texto longo e cuidadoso que ensina o Claude a pensar como um tributarista sênior brasileiro. **Esta peça é construída COM o Jefferson** — ele traz o conhecimento de domínio, o Claude Code estrutura. É aqui que mora o valor da MAGUS.
3. **Ligação com o motor** — código que envia o prompt e recebe a resposta.

### O que o Protótipo 0 NÃO faz (deixar claro se o tema surgir)

- Não processa arquivos SPED/ECF/ECD reais (isso é v1)
- Não tem login, multiusuário, banco de dados (isso é v1)
- Não está conectado a bases jurídicas atualizadas (isso é v1+)
- Não é seguro para dados sigilosos reais — **usar SEMPRE dados fictícios ou anonimizados nos testes**

---

## Decisões já tomadas (não reabrir sem motivo)

- **Marca:** MAGUS.IA (logo: Conceito C3 — Glifo Abstrato). Filing INPI em andamento.
- **Estrutura societária:** MAGUS IA TECNOLOGIA LTDA, dentro da ABM Holding, porte "DEMAIS".
- **Não treinar modelo do zero.** Construir aplicação vertical sobre modelo existente.
- **Não usar localStorage/browser storage** em protótipos.
- **Stack do Protótipo 0:** Python + Streamlit + API Anthropic. Decidido.
- **Modo de trabalho:** Jefferson aprende e constrói, com assistência. Para a SaaS de produção, há recomendação aberta de trazer reforço técnico no futuro.

---

## Guardrails — regras de segurança

1. **Chave de API:** sempre em `.env`, sempre no `.gitignore`. Nunca exibir, nunca versionar, nunca colar em texto compartilhável.
2. **Dados de teste:** APENAS dados fictícios ou anonimizados. Nada de dados reais de clientes do escritório do Jefferson no protótipo.
3. **Limite de gasto:** a conta Anthropic Console deve ter limite de gasto mensal definido. Lembrar o Jefferson de monitorar.
4. **Backups:** commits frequentes quando o Git entrar em uso. Antes disso, não deixar trabalho não-salvo acumular.

---

## Documentos de referência (nesta mesma pasta)

- `Prototipo_0_Visao.md` — visão completa do que estamos construindo e por quê
- `Guia_Setup_Ambiente.md` — passo a passo do setup do ambiente (referência; o Claude Code pode automatizar boa parte)
- `Glossario_Tecnico.md` — todos os termos técnicos explicados em português acessível

### Onde mora cada coisa (arquitetura de pastas)

- **Código do Protótipo 0:** pasta local `~/magus-fiscal` no Mac Mini M4 (esta pasta). Fica FORA do Google Drive de propósito — o Google Drive não foi feito para sincronizar projetos de código (ambiente virtual, milhares de arquivos, churn constante de sincronização). O backup do código será feito via Git/GitHub mais adiante.
- **Documentos de estratégia, marca e jurídico:** pasta "Projeto Bilhão" no Google Drive, conduzidos na sessão do Cowork. Caminho no Mac: `~/Library/CloudStorage/GoogleDrive-advocaciajeffersonalves@gmail.com/Meu Drive/10. CLAUDE CODE/Projeto Bilhão/`. Lá estão o `01_Plano_Estrategico_v1.md`, a pasta `00_MAGUS_Marca/` e a transcrição completa do projeto.
- Os arquivos de referência desta pasta (`CLAUDE.md`, `Prototipo_0_Visao.md`, `Guia_Setup_Ambiente.md`, `Glossario_Tecnico.md`) são cópias trazidas da pasta `01_MAGUS_Fiscal/Desenvolvimento/` do Google Drive. Se precisar de contexto estratégico mais amplo, peça ao Jefferson — ele acessa o Drive pelo Cowork.

---

## Estado atual e próximo passo

**Estado:** base de desenvolvimento documentada. Claude Code instalado e autenticado no Mac Mini M4 (14/05/2026). Esta pasta de trabalho (`~/magus-fiscal`) é local, fora do Google Drive. Ambiente Python ainda NÃO montado.

**Próximo passo:** o Claude Code, ao iniciar, deve:
1. Cumprimentar o Jefferson, confirmar que leu este briefing, e confirmar com ele se já tem conta no Anthropic Console e chave de API. **Atenção:** a chave de API é coisa separada do login do Claude Code — o Protótipo 0 precisa de uma chave de API própria para conseguir chamar o Claude. Se ele ainda não tiver, orientar a criar em console.anthropic.com com limite de gasto mensal definido.
2. Ajudar a montar o ambiente (verificar/instalar Python via Homebrew, criar ambiente virtual, instalar as bibliotecas `anthropic`, `streamlit`, `python-dotenv`) — fazer via terminal, explicando cada passo, sem despejar tudo de uma vez.
3. Validar com um teste mínimo que a API responde.
4. Só então partir para a construção do esqueleto do Protótipo 0 (interface Streamlit + ligação com a API).
5. Depois, a peça central: construir COM o Jefferson o system prompt de especialização tributária.

**Ritmo:** sem pressa. Cada etapa confirmada antes da próxima. O Jefferson está aprendendo — o processo importa tanto quanto o resultado.

---

## Sincronização com a sessão de planejamento (Cowork)

A estratégia, marca, jurídico e planejamento de negócio são conduzidos numa sessão separada (Cowork desktop). Este arquivo CLAUDE.md é a ponte de contexto. Quando houver decisão estratégica relevante tomada na construção, registrar aqui para manter os dois mundos sincronizados.

---

**Versão:** 1.1
**Criado em:** maio de 2026, pela sessão de planejamento (Cowork), para handoff ao Claude Code.
**Atualizado:** 14/05/2026 — Claude Code instalado e autenticado no Mac Mini; arquitetura de pastas registrada (código local em `~/magus-fiscal`, estratégia no Google Drive).
