# Guia — Sincronizar o Projeto via Google Drive

> *Objetivo: deixar a pasta "Projeto Bilhão" sincronizada entre a máquina Windows (onde roda o Cowork) e o Mac Mini (onde vai rodar o Claude Code). Assim os dois trabalham nos mesmos arquivos, sempre atualizados.*

---

## Como vai funcionar

A pasta "Projeto Bilhão" vai morar dentro do Google Drive. O Google Drive para Desktop, instalado nas duas máquinas com a mesma conta Google, mantém a pasta idêntica nos dois lugares automaticamente. Você edita num lado, aparece no outro.

**Conta a usar:** a mesma do email institucional ou a sua conta Google pessoal. Recomendo manter consistência — se for usar para a empresa, considere a conta vinculada ao MAGUS.IA no futuro, mas por ora qualquer conta Google sua funciona.

**Espaço:** o Google Drive gratuito tem 15 GB. O projeto inteiro hoje tem poucos MB (textos, alguns PNGs). Espaço não é problema.

---

## PARTE 1 — No computador Windows (onde roda o Cowork)

### Passo 1 — Instalar o Google Drive para Desktop

1. Abra o navegador e vá em: [google.com/drive/download](https://www.google.com/drive/download/)
2. Baixe o **"Drive para computador"** (Google Drive for Desktop).
3. Abra o arquivo baixado e instale (avançar, avançar, concluir).
4. Reinicie o computador se ele pedir.

### Passo 2 — Fazer login

1. Após instalar, o Google Drive abre uma janela de login.
2. Entre com sua conta Google.
3. Autorize o acesso.

### Passo 3 — Localizar o Google Drive no computador

1. Abra o **Explorador de Arquivos** (a pastinha amarela na barra de tarefas).
2. Na lateral esquerda, vai aparecer um novo item: **"Google Drive"** (geralmente como uma unidade, tipo `G:`).
3. Dentro dele há a pasta **"Meu Drive"** (My Drive).

### Passo 4 — Mover a pasta "Projeto Bilhão" para o Google Drive

1. No Explorador de Arquivos, navegue até onde está a pasta hoje:
   `C:\Users\Admin\Documents\Claude\Projects\`
2. Clique com o botão direito na pasta **"Projeto Bilhão"** → **Recortar**.
3. Navegue até **"Google Drive" → "Meu Drive"**.
4. Clique com o botão direito num espaço vazio → **Colar**.
5. A pasta vai começar a subir para a nuvem. Aguarde os ícones de **check verde** aparecerem em todos os arquivos — isso indica que a sincronização terminou.

> **Dica:** se quiser organização, pode criar uma subpasta dentro do "Meu Drive" chamada `MAGUS` e colocar a "Projeto Bilhão" dentro dela. Mas não é obrigatório.

### Passo 5 — Re-apontar o Cowork para o novo local

Como você moveu a pasta, o Cowork precisa saber o novo endereço dela.

1. Nas configurações do Cowork, há a opção de **selecionar/trocar a pasta de trabalho** (foi por ela que você escolheu essa pasta no início).
2. Selecione a pasta "Projeto Bilhão" no **novo local**, dentro do Google Drive.
3. Pode ser necessário **reiniciar o Cowork** para ele reconhecer o novo caminho.

> **Se você tiver qualquer dificuldade nesta etapa específica de re-apontar o Cowork, me avise** — é o único passo que pode ter alguma variação na interface. Os outros são diretos.

---

## PARTE 2 — No Mac Mini M4

### Passo 6 — Instalar o Google Drive para Desktop (versão Mac)

1. No Mac Mini, abra o navegador e vá em: [google.com/drive/download](https://www.google.com/drive/download/)
2. Baixe a versão para **macOS**.
3. Abra o arquivo baixado (`.dmg`).
4. Arraste o ícone do Google Drive para a pasta **Aplicativos**.
5. Abra o Google Drive pela primeira vez (pode aparecer um aviso de segurança do macOS — confirme que quer abrir).

### Passo 7 — Fazer login com a MESMA conta

1. O Google Drive vai pedir login.
2. Entre com **exatamente a mesma conta Google** usada no Windows. Isso é o que conecta as duas máquinas.
3. Autorize o acesso.

### Passo 8 — Encontrar a pasta sincronizada

1. Abra o **Finder** (o rosto sorridente azul no Dock).
2. Na lateral esquerda, vai aparecer **"Google Drive"**.
3. Dentro dele, **"Meu Drive"**, e lá estará a pasta **"Projeto Bilhão"** — a mesma que está no Windows.
4. Na primeira vez, pode levar alguns minutos para baixar tudo. Aguarde.

### Passo 9 — Deixar a pasta disponível offline (importante para o Claude Code)

Por padrão, o Google Drive "transmite" os arquivos (baixa sob demanda). Para o Claude Code trabalhar bem, é melhor ter os arquivos baixados localmente.

1. No Finder, dentro do Google Drive, clique com o botão direito na pasta **"Projeto Bilhão"**.
2. Procure a opção **"Disponível off-line"** (Available offline) e ative.
3. Aguarde o download completar.

---

## PARTE 3 — Pronto. Como fica daqui em diante

✅ As duas máquinas veem a mesma pasta "Projeto Bilhão".
✅ Você edita no Cowork (Windows) → sincroniza para o Mac.
✅ O Claude Code cria código no Mac → sincroniza para o Windows.
✅ Tudo num lugar só, sempre atualizado.

**No Mac Mini, para iniciar o Claude Code:** abra o Terminal e navegue até a pasta de desenvolvimento dentro do Google Drive. O caminho será algo como:
```
cd ~/Google\ Drive/Meu\ Drive/Projeto\ Bilhão/01_MAGUS_Fiscal/Desenvolvimento/
```
(o caminho exato pode variar — o Claude Code te ajuda a encontrar se você pedir)

Depois rode `claude` e ele lê o CLAUDE.md automaticamente.

---

## Cuidados importantes

1. **Não edite o mesmo arquivo nas duas máquinas ao mesmo tempo.** O Google Drive sincroniza bem, mas edição simultânea do mesmo arquivo pode gerar conflito (ele cria uma cópia "em conflito"). Na prática: trabalhe estratégia no Cowork, código no Mac — frentes diferentes, sem colisão.

2. **Espere a sincronização terminar antes de trocar de máquina.** Olhe os ícones de check verde. Se você fechar o computador antes de sincronizar, a outra máquina não recebe a atualização.

3. **A primeira sincronização no Mac pode demorar alguns minutos.** Tenha paciência — é só uma vez.

4. **Mantenha o Google Drive aberto/rodando** nas duas máquinas durante o trabalho. Ele roda em segundo plano (ícone na barra de tarefas/menu superior).

---

## Resumo em uma linha

Instalar Google Drive para Desktop nas duas máquinas → mesma conta → mover "Projeto Bilhão" para o Drive no Windows → re-apontar o Cowork → no Mac a pasta aparece sozinha → rodar o Claude Code de dentro dela.

---

**Versão:** 1.0
**Se travar em qualquer passo:** me avise qual passo e o que apareceu na tela.
