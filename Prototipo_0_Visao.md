# MAGUS Fiscal — Protótipo 0: Visão

> *O que vamos construir juntos, por quê, e o que ele NÃO é (ainda).*

---

## O que é o Protótipo 0

**Nome de trabalho:** "Analista Tributário Assistido"

É a primeira versão funcional do MAGUS Fiscal. Um programa que roda no seu Mac Mini, abre no navegador, e faz o seguinte:

1. **Você descreve** a situação tributária de uma empresa — setor, regime tributário, faturamento aproximado, atividades, e a dúvida ou objetivo específico.
2. **O MAGUS analisa** usando um motor de IA (Claude) com uma camada de especialização tributária que nós vamos projetar.
3. **O MAGUS devolve** uma análise estruturada:
   - Créditos tributários que merecem investigação
   - Riscos fiscais identificados
   - Oportunidades de planejamento tributário
   - Esboço de um parecer preliminar
   - Próximas perguntas e documentos necessários para aprofundar

É o conceito da MAGUS em miniatura: **IA vertical, especialista, brasileira.** A "inteligência" não vem de treinar um modelo — vem da camada de especialização que você, o tributarista, vai projetar comigo.

---

## Por que começar por aqui

**Prova o conceito.** Deixa de ser ideia, vira coisa que funciona e que você pode mostrar.

**É sua ferramenta de recrutamento.** Quando você for buscar reforço técnico, mostrar um protótipo que funciona vale 10x mais que um pitch.

**É seu demo para design partners.** Nas 40 entrevistas, poder dizer "olha, é isso aqui" muda a conversa.

**Te ensina na prática.** Você vai entender — de verdade, com as mãos — o que significa construir uma aplicação de IA. Os termos vão deixar de ser abstratos.

**Valida a tese central.** Se o Protótipo 0 produzir análises tributárias úteis, a tese da MAGUS está provada. Se não produzir, descobrimos cedo e barato.

---

## O que o Protótipo 0 NÃO é (ainda)

Para não criar expectativa errada — o Protótipo 0 deliberadamente **não** faz, nesta primeira versão:

- **Não processa arquivos SPED, ECF, ECD reais.** Isso é um pipeline de processamento de documentos que entra na v1. No Protótipo 0, a entrada é texto estruturado que você digita ou cola.
- **Não tem login, multiusuário, cadastro.** É uma ferramenta local, só sua, para validar o conceito.
- **Não está conectado a bases de dados jurídicas atualizadas.** O conhecimento vem do modelo de IA + da camada de especialização que escrevemos. Conexão com legislação em tempo real é v1+.
- **Não é seguro para dados sigilosos de clientes reais ainda.** Use dados fictícios ou anonimizados nos testes. Segurança de produção vem depois.
- **Não é o produto final.** É o esqueleto que prova que o corpo pode existir.

Pensa nele como o **primeiro voo de um protótipo de avião**: não transporta passageiros, mas prova que a coisa levanta do chão.

---

## A arquitetura em linguagem simples

```
   VOCÊ
    │  (descreve a situação tributária)
    ▼
┌─────────────────────────────┐
│   INTERFACE (Streamlit)     │  ← a tela que abre no navegador
│   roda no seu Mac Mini      │
└─────────────────────────────┘
    │  (envia sua descrição + a camada de especialização)
    ▼
┌─────────────────────────────┐
│   MOTOR DE IA (Claude)      │  ← o "cérebro" bruto, acessado via API
│   na nuvem da Anthropic     │
└─────────────────────────────┘
    │  (devolve a análise)
    ▼
┌─────────────────────────────┐
│   INTERFACE mostra o        │
│   resultado estruturado     │
└─────────────────────────────┘
    │
    ▼
   VOCÊ  (lê, avalia como especialista, ajusta)
```

**As 3 peças que você vai controlar:**

1. **A interface** (Streamlit) — onde você digita e lê os resultados. Código simples em Python.
2. **A camada de especialização** — o "system prompt": um texto longo e cuidadoso que ensina o motor de IA a pensar como um tributarista sênior. **Esta é a peça mais importante, e é 100% domínio seu.** É aqui que sua expertise vira código.
3. **A ligação com o motor** — algumas linhas de código que mandam a pergunta para o Claude e recebem a resposta.

A peça 2 é onde mora a mágica da MAGUS. As peças 1 e 3 são "encanamento" — importantes, mas padronizadas.

---

## O caminho até o Protótipo 0 funcionando

| Fase | O que acontece | Quem faz |
|------|----------------|----------|
| **A — Setup** | Preparar o Mac Mini: Python, editor de código, chave de API | Você, seguindo o Guia de Setup, eu acompanhando |
| **B — Esqueleto** | Construir a interface mínima + ligação com o motor de IA | Eu escrevo o código, você roda e testa |
| **C — Camada de especialização** | Projetar o system prompt — a expertise tributária. Várias rodadas. | Nós dois juntos — você traz o conhecimento, eu estruturo |
| **D — Testes reais** | Você testa com cenários tributários reais (dados fictícios), avalia a qualidade | Você como especialista, eu ajustando |
| **E — Refinamento** | Iterar até a análise ficar consistentemente útil | Nós dois |

Estimativa: com sessões focadas, o Protótipo 0 funcionando em **2 a 4 semanas** de trabalho intercalado.

---

## O que você precisa providenciar

1. **Tempo**: blocos de 1-2 horas, algumas vezes por semana.
2. **Chave de API da Anthropic**: conta + cartão de crédito. Custo de prototipagem: baixo, provavelmente US$ 10-50 no total da fase de protótipo.
3. **Mac Mini M4 ligado e disponível**: é onde tudo roda.
4. **Disposição de aprender termos novos**: o Glossário Técnico está na mesma pasta para consulta.
5. **3 a 5 cenários tributários reais** (com dados fictícios/anonimizados) para testar — você já tem esses na cabeça, do seu dia a dia de escritório.

---

## Próximo passo imediato

Abra o documento **`Guia_Setup_Ambiente.md`** (mesma pasta) e siga os passos. É a Fase A. Quando concluir cada etapa, me avise — eu acompanho e resolvo qualquer travamento.

Quando o setup estiver pronto, partimos para a Fase B e eu começo a escrever o código do esqueleto.

---

**Versão:** 1.0
**Próxima revisão:** após conclusão do setup do ambiente
