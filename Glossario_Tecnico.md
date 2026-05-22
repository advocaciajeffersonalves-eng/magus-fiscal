# MAGUS Fiscal — Glossário Técnico

> *Os termos que você vai encontrar na construção, explicados em português claro. Consulte sempre que aparecer uma palavra nova. Este documento cresce conforme avançamos.*

---

## Termos que você vai usar JÁ no Protótipo 0

### IA / Inteligência Artificial
Termo amplo. No nosso caso, refere-se especificamente aos **modelos de linguagem** (ver "LLM" abaixo). Quando dizemos "o MAGUS usa IA", queremos dizer que ele usa um modelo de linguagem como motor de raciocínio.

### LLM (Large Language Model / Grande Modelo de Linguagem)
É o "cérebro" de base. Um sistema treinado em enormes quantidades de texto que consegue ler, entender e gerar linguagem — incluindo raciocínio complexo. Claude (da Anthropic) e GPT (da OpenAI) são LLMs. **Você não vai construir um LLM** — vai usar um pronto, como motor.

### Modelo
Uma versão específica de um LLM. Por exemplo: `claude-sonnet-4-6`, `claude-opus-4-6`. Modelos diferentes têm capacidades e custos diferentes — uns são mais rápidos e baratos, outros mais poderosos e caros. No protótipo, vamos começar com o Sonnet (bom equilíbrio) e usar o Opus quando precisarmos de raciocínio mais profundo.

### API (Application Programming Interface)
É a "porta de entrada" para usar o LLM pelo seu código. Em vez de abrir o Claude no navegador e conversar, seu programa "conversa" com o Claude automaticamente, através da API. Pense na API como um garçom: seu código faz o pedido, a API leva até a cozinha (o modelo), e traz a resposta de volta.

### Chave de API (API Key)
A "senha" que identifica e autoriza você a usar a API. É como o cartão de crédito do serviço — é por ela que o uso é cobrado, e por isso ela **nunca pode ser compartilhada ou publicada**. Parece com `sk-ant-api03-xxxx...`.

### Token
A unidade de medida do texto para um LLM. Aproximadamente, **1 token ≈ 4 caracteres** ou cerca de ¾ de uma palavra. Importa porque **o custo da API é cobrado por token** — tanto o texto que você envia quanto o que o modelo responde. Um parecer de uma página tem uns 500-800 tokens. Saber disso ajuda a entender e controlar custos.

### Prompt
O texto que você envia para o modelo. É a "pergunta" ou "instrução". A qualidade do prompt determina enormemente a qualidade da resposta. "Engenharia de prompt" é a habilidade de escrever bons prompts.

### System Prompt (Prompt de Sistema)
Um prompt especial que define **quem o modelo é e como ele deve se comportar** durante toda a conversa. É aqui que mora a "camada de especialização" da MAGUS. No Protótipo 0, o system prompt vai ser um texto longo e cuidadoso que ensina o Claude a pensar como um tributarista sênior brasileiro. **Esta é a peça mais importante e mais sua** — sua expertise vira texto aqui.

### Inferência
O ato do modelo "pensar" e gerar uma resposta. Quando você manda um prompt e o modelo responde, isso é "uma inferência". Cada inferência custa tokens (dinheiro) e leva alguns segundos.

### Python
A linguagem de programação que vamos usar. É a linguagem padrão mundial para aplicações de IA — relativamente legível, com muitas ferramentas prontas. Você não precisa virar especialista em Python; precisa entender o suficiente para ler, ajustar e rodar o código que construímos juntos.

### Biblioteca (Library)
Um conjunto de código pronto que outras pessoas escreveram e que você "importa" para usar. Em vez de programar tudo do zero, você usa bibliotecas. Exemplos no nosso projeto: `anthropic` (conecta ao Claude), `streamlit` (cria a interface).

### Terminal
O programa de linha de comando do Mac, onde você digita instruções de texto em vez de clicar em botões. Parece intimidante no começo, mas você vai usar só um punhado de comandos repetidamente.

### Comando
Uma instrução de texto que você digita no Terminal e executa pressionando `Enter`. Exemplo: `python teste.py` é um comando que manda o Python rodar o arquivo `teste.py`.

### Homebrew
Um "instalador de programas" para Mac, voltado a ferramentas de desenvolvimento. Em vez de baixar e instalar manualmente, você roda `brew install nome-do-programa`.

### Ambiente Virtual (venv)
Uma "caixa isolada" para o seu projeto. Cada projeto tem o seu ambiente virtual, com suas próprias bibliotecas, sem interferir nos outros nem no sistema. Boa prática universal. Você "ativa" o ambiente antes de trabalhar (`source venv/bin/activate`).

### VS Code (Visual Studio Code)
O editor de código que vamos usar. É como um "Word para programadores" — onde você escreve, organiza e navega pelo código. Gratuito, da Microsoft, padrão da indústria.

### Streamlit
Uma biblioteca Python que transforma código simples numa interface visual que abre no navegador. Com Streamlit, em poucas linhas você tem caixas de texto, botões e áreas de resultado — sem precisar saber design web. Perfeito para protótipos.

### Arquivo `.env`
Um arquivo de configuração onde guardamos informações sensíveis — principalmente a chave de API — de forma separada do código. Assim a chave nunca aparece no código que pode ser compartilhado.

---

## Termos que vão aparecer mais à frente (v1 e além)

### RAG (Retrieval-Augmented Generation)
Técnica de "dar memória e fontes" ao modelo. Em vez de o modelo responder só com o que "sabe", ele primeiro **busca** informações relevantes numa base de dados (legislação, jurisprudência, documentos do cliente) e **depois** responde com base nelas. É como dar ao tributarista uma biblioteca consultável em vez de só a memória. Será essencial no MAGUS v1.

### Embedding
Uma forma de transformar texto em números, de um jeito que o computador consiga medir "o quão parecidos" dois textos são em significado. É a tecnologia por trás da busca inteligente do RAG. Não precisa entender a matemática — só saber que é o que permite "encontrar o artigo de lei relevante" automaticamente.

### Base de Conhecimento (Knowledge Base)
A coleção organizada de documentos que o MAGUS consulta — legislação tributária, jurisprudência, manuais, decisões do CARF. Construir e manter essa base é parte central do valor do produto.

### Fine-tuning (Ajuste fino)
Treinar um pouco mais um modelo existente, com seus próprios exemplos, para especializá-lo. Diferente de treinar do zero. Pode ser útil no futuro, mas **não é prioridade** — o system prompt + RAG resolvem 90% das necessidades com muito menos custo e complexidade.

### Backend e Frontend
**Frontend** é a parte que o usuário vê e usa (a interface). **Backend** é a parte que faz o trabalho pesado nos bastidores (processamento, banco de dados, lógica). No Protótipo 0, o Streamlit faz os dois de forma simplificada. Numa SaaS de produção, eles são separados.

### Banco de Dados
Onde a aplicação guarda informação de forma organizada e permanente — usuários, documentos, históricos de análise. O Protótipo 0 não precisa de um; a v1 vai precisar.

### Deploy / Hospedagem
Colocar a aplicação "no ar" para outras pessoas usarem, normalmente num servidor na nuvem. O Protótipo 0 roda só no seu Mac. A v1, para os design partners, vai precisar de deploy.

### Nuvem (Cloud)
Servidores de terceiros (AWS, Google Cloud, Azure) que você aluga em vez de manter máquinas próprias. Para uma SaaS que precisa estar disponível 24/7 com segurança e escala, a nuvem quase sempre vence o servidor próprio.

### API REST / Endpoint
Quando a MAGUS virar produto, ela própria terá uma API — uma porta para outros sistemas se conectarem a ela. Cada "porta" específica é um endpoint. Relevante na fase de produto, não no protótipo.

### Git e Repositório
Git é um sistema de "controle de versão" — guarda o histórico de todas as mudanças no código, permite voltar atrás, e permite várias pessoas trabalharem juntas. Um "repositório" é o projeto versionado pelo Git. Vamos usar quando o código crescer.

### LGPD (no contexto técnico)
A Lei Geral de Proteção de Dados afeta diretamente a arquitetura: dados fiscais de clientes são sensíveis. Onde os dados ficam armazenados, como são transmitidos, quem tem acesso, e o que os fornecedores de IA fazem com eles — tudo isso entra no desenho técnico da v1. No Protótipo 0, a regra é simples: **use só dados fictícios ou anonimizados**.

---

## Como usar este glossário

- Quando aparecer um termo que você não conhece numa conversa nossa ou num documento, procure aqui primeiro.
- Se o termo não estiver aqui, me pergunte — eu explico e adiciono ao glossário.
- Não tente decorar tudo de uma vez. Os termos vão "grudar" naturalmente conforme você os usa na prática.

---

**Versão:** 1.0
**Atualização:** este documento cresce conforme novos termos aparecem no desenvolvimento.
