# MAGUS Fiscal — Guia de Setup do Ambiente (Mac Mini M4)

> *Passo a passo para preparar seu Mac Mini para o desenvolvimento. Feito para quem nunca programou. Siga na ordem. Quando travar em algum ponto, me avise — eu resolvo com você.*

---

## Antes de começar — o que você vai instalar e por quê

Vamos instalar 4 coisas no seu Mac Mini. Não precisa entender tudo agora — só saber o papel de cada uma:

| Ferramenta | O que é | Por que precisamos |
|------------|---------|--------------------|
| **Terminal** | Um programa que já vem no Mac, onde você digita comandos | É por onde instalamos e rodamos as coisas |
| **Homebrew** | Um "instalador de programas para desenvolvedores" | Facilita instalar Python e outras ferramentas |
| **Python** | A linguagem de programação que vamos usar | É a linguagem padrão para aplicações de IA |
| **VS Code** | Um editor de código (tipo um Word para programadores) | É onde vamos escrever e organizar o código |
| **Chave de API Anthropic** | Uma "senha" que dá acesso ao motor de IA (Claude) | É o "cérebro" que o MAGUS vai usar |

Tempo total estimado: **45 a 90 minutos**, sem pressa.

---

## PASSO 1 — Abrir o Terminal

O Terminal é um programa que já está no seu Mac.

1. Pressione `Command (⌘) + barra de espaço` — abre a busca do Mac (Spotlight).
2. Digite `Terminal` e pressione `Enter`.
3. Vai abrir uma janela com fundo claro ou escuro e um texto com o nome do seu usuário, terminando com `$` ou `%`.

**O que você vai ver:** algo como `jefferson@MacMini ~ %`. Esse símbolo `%` (ou `$`) significa "estou pronto, pode digitar um comando".

**Dica:** quando eu pedir para "rodar um comando", significa: copiar o texto, colar no Terminal, e pressionar `Enter`.

---

## PASSO 2 — Instalar o Homebrew

O Homebrew é o instalador que vai facilitar tudo o resto.

1. No Terminal, cole este comando exatamente e pressione `Enter`:

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. Ele vai pedir sua **senha do Mac** (a mesma que você usa para desbloquear o computador). Digite — ela não aparece na tela enquanto você digita, isso é normal. Pressione `Enter`.

3. Ele vai pedir confirmação. Pressione `Enter` novamente quando solicitado.

4. A instalação leva alguns minutos. Vai aparecer bastante texto correndo na tela — normal.

5. **Ao final**, ele pode mostrar duas linhas que começam com `echo` e pedir para você rodá-las. Se aparecerem, copie e rode cada uma. Se tiver dúvida, me mande o print da tela.

**Como saber se deu certo:** rode este comando:
```
brew --version
```
Se aparecer algo como `Homebrew 4.x.x`, funcionou. Se der erro "command not found", me avise — resolvemos juntos.

---

## PASSO 3 — Instalar o Python

Com o Homebrew pronto, instalar o Python é um comando só:

```
brew install python
```

Leva 2-5 minutos.

**Como saber se deu certo:** rode:
```
python3 --version
```
Deve aparecer algo como `Python 3.12.x` ou superior. Anote a versão.

---

## PASSO 4 — Instalar o VS Code (editor de código)

1. Rode no Terminal:
```
brew install --cask visual-studio-code
```

2. Leva alguns minutos.

3. **Como saber se deu certo:** abra o Spotlight (`⌘ + espaço`), digite `Visual Studio Code` e veja se o programa abre.

**Alternativa:** se o comando der problema, você pode baixar manualmente em [code.visualstudio.com](https://code.visualstudio.com) — é só baixar, abrir o arquivo e arrastar para a pasta Aplicativos.

---

## PASSO 5 — Criar a conta e a chave de API da Anthropic

Esta é a peça que dá acesso ao "cérebro" (Claude). É um serviço pago por uso — na fase de protótipo, o custo é baixo (provavelmente US$ 10-50 no total).

### 5.1 Criar a conta

1. Acesse [console.anthropic.com](https://console.anthropic.com)
2. Clique em "Sign up" e crie sua conta (pode usar o email `juridico@magus.ia.br` ou seu email pessoal).
3. Confirme o email.

### 5.2 Adicionar forma de pagamento e definir limite de segurança

1. Dentro do console, procure por "Billing" (Faturamento) ou "Plans".
2. Adicione um cartão de crédito.
3. **Importante — segurança:** procure a opção de definir um **limite de gasto mensal** (spend limit / usage limit). Defina algo baixo no começo, como **US$ 20 ou US$ 30**. Isso impede qualquer surpresa na fatura. Dá para aumentar depois.

### 5.3 Gerar a chave de API

1. No console, procure por "API Keys".
2. Clique em "Create Key" (Criar Chave).
3. Dê um nome, por exemplo: `MAGUS-Prototipo-0`.
4. **ATENÇÃO CRÍTICA:** a chave aparece **uma única vez**. Copie e guarde em local seguro AGORA — um gerenciador de senhas, ou um arquivo de texto protegido. Se perder, é só gerar outra, mas não dá para "ver de novo" a mesma.
5. A chave parece com isto: `sk-ant-api03-xxxxxxxxxxxxx...` (uma sequência longa).

**Regra de ouro da chave de API:** ela é como a senha do seu cartão. **Nunca** publique, nunca mande por mensagem, nunca coloque em um site público, nunca suba para o GitHub. Vamos guardá-la de forma segura no Passo 7.

---

## PASSO 6 — Criar a pasta do projeto

1. No Terminal, rode estes comandos, um de cada vez:

```
mkdir -p ~/MAGUS-Fiscal/prototipo-0
```
```
cd ~/MAGUS-Fiscal/prototipo-0
```

O primeiro cria a pasta. O segundo "entra" nela (`cd` = change directory).

2. Abra essa pasta no VS Code:
```
code .
```
(é o comando `code` seguido de um ponto — o ponto significa "a pasta atual"). O VS Code vai abrir mostrando a pasta do projeto.

---

## PASSO 7 — Criar o ambiente virtual e instalar as bibliotecas

### 7.1 O que é um "ambiente virtual"

Pense num ambiente virtual como uma **caixa isolada** para o seu projeto. Cada projeto tem a sua caixa, com suas próprias ferramentas, sem bagunçar o resto do computador. É boa prática universal.

### 7.2 Criar o ambiente virtual

No Terminal (certifique-se de que está dentro da pasta do projeto — o Passo 6.1 já te colocou lá), rode:

```
python3 -m venv venv
```

Isso cria a "caixa isolada" (uma pasta chamada `venv`).

### 7.3 Ativar o ambiente virtual

```
source venv/bin/activate
```

**Como saber se ativou:** o início da linha do Terminal vai passar a mostrar `(venv)` antes do seu nome de usuário. Sempre que for trabalhar no projeto, ative o ambiente assim.

### 7.4 Instalar as bibliotecas

Com o ambiente ativado (`(venv)` aparecendo), rode:

```
pip install anthropic streamlit python-dotenv
```

O que cada uma faz:
- **anthropic** — conecta seu código ao motor de IA Claude
- **streamlit** — cria a interface visual que abre no navegador
- **python-dotenv** — guarda a chave de API de forma segura

Leva 1-2 minutos.

---

## PASSO 8 — Guardar a chave de API com segurança

1. No VS Code, com a pasta do projeto aberta, crie um arquivo novo chamado exatamente:
```
.env
```
(sim, começa com um ponto — isso o torna um arquivo "de configuração")

2. Dentro do arquivo `.env`, escreva uma linha assim, colando sua chave real no lugar do texto:
```
ANTHROPIC_API_KEY=sk-ant-api03-suachaverealaqui
```

3. Salve o arquivo (`⌘ + S`).

4. Crie outro arquivo chamado `.gitignore` e escreva dentro:
```
.env
venv/
```
Isso garante que, no futuro, se você usar Git, a chave nunca seja publicada por acidente.

---

## PASSO 9 — Teste final: confirmar que tudo funciona

Vamos rodar um teste pequeno para confirmar que o motor de IA responde.

1. No VS Code, crie um arquivo chamado `teste.py`.

2. Cole este código dentro:

```python
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

resposta = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=200,
    messages=[
        {"role": "user", "content": "Responda em uma frase: o que é engenharia tributária?"}
    ]
)

print(resposta.content[0].text)
```

3. Salve (`⌘ + S`).

4. No Terminal (com `(venv)` ativado e dentro da pasta do projeto), rode:
```
python teste.py
```

5. **Se tudo estiver certo**, em alguns segundos vai aparecer uma frase explicando o que é engenharia tributária — gerada pelo Claude. 🎯

**Se der erro**, copie a mensagem de erro inteira e me mande. Erros nessa etapa são comuns e quase sempre rápidos de resolver (geralmente é a chave de API com algum caractere a mais, ou o ambiente virtual não ativado).

---

## Checklist de conclusão do setup

- [ ] Terminal aberto e funcionando
- [ ] Homebrew instalado (`brew --version` responde)
- [ ] Python instalado (`python3 --version` responde 3.12+)
- [ ] VS Code instalado e abrindo
- [ ] Conta Anthropic criada
- [ ] Limite de gasto mensal definido (segurança)
- [ ] Chave de API gerada e guardada em local seguro
- [ ] Pasta do projeto criada (`~/MAGUS-Fiscal/prototipo-0`)
- [ ] Ambiente virtual criado e ativado (`(venv)` aparece)
- [ ] Bibliotecas instaladas (anthropic, streamlit, python-dotenv)
- [ ] Arquivo `.env` criado com a chave
- [ ] Arquivo `.gitignore` criado
- [ ] Teste final rodou e o Claude respondeu

**Quando todos os itens estiverem marcados**, me avise. Aí partimos para a Fase B — eu começo a escrever o código do esqueleto do Protótipo 0.

---

## Quando travar — como me pedir ajuda

Travamento em setup é absolutamente normal, inclusive para programadores experientes. Quando acontecer:

1. **Não tente "consertar adivinhando"** — pode complicar.
2. **Copie a mensagem de erro inteira** (todo o texto vermelho/de erro que aparecer).
3. **Me mande**: em qual passo travou + a mensagem de erro + um print da tela se possível.
4. Eu te dou o próximo passo exato.

Não existe pergunta boba aqui. Cada travamento resolvido é aprendizado real.

---

**Versão:** 1.0
**Próximo documento:** após o setup, partimos para o código do esqueleto (Fase B)
