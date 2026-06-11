# MAGUS Fiscal — Status do Projeto

> Documento de referência: o que foi construído, onde está, como rodar e como continuar.
> Atualizado em 11/06/2026.

## Visão
Plataforma de inteligência fiscal/jurídica para advogados, contadores e empresários —
com foco em **fiscal internacional Brasil–EUA**. Roda **local no Mac Mini** (Streamlit + Python),
exposta em **magusfiscal.com.br** via Cloudflare Tunnel. Custo de IA minimizado:
templates e busca local são **grátis**; IA generativa (Sonnet) só quando necessário.
**Fase atual:** demo de plataforma para captar investidor — não expandir até ter investimento.

## Módulos da ferramenta (sidebar)
| Módulo | Arquivo | O que faz | Custo |
|---|---|---|---|
| Saída Fiscal Brasil→EUA | `app.py` (modulo transicao) + `diagnostico_engine.py` | diagnóstico de residência fiscal: classificação, risco 0-100, alertas, relatório DOCX 13 seções | grátis (motor) |
| Gerador de Contratos | `contratos.py` + `templates_engine.py` | 78 tipos, wizard guiado, template-first | grátis (preenche) / Sonnet (gerar novo) |
| Gerador de Defesas | `defesas.py` + `app.py` (modulo defesas) | cola/anexa/**fotografa** autuação → impugnação com legislação + jurisprudência CARF | foto: IA visão; texto: Sonnet |
| Meus Clientes (CRM) | `crm.py` + `app.py` (modulo clientes) | ficha de cliente + histórico de serviços; vincula documentos gerados | grátis |
| Painel | `app.py` (modulo dashboard) | métricas de clientes/serviços | grátis |

## Acervo de conhecimento (RAG local — `rag_local.py`)
- Backend **numpy** (`templates/_doutrina/rag_embeddings.npy` + `rag_textos.json`), busca vetorizada, indexação incremental (`rag.adicionar`).
- Conteúdo: doutrina civil destilada + **Vade Mecum** (CC, CPC, CTN, CDC, CLT…) + leis imobiliárias + **legislação fiscal** (Lei 14.754, IN 208/2002, IN 2.180, SC Cosit 56, Perguntão IRPF) + **201 normas RFB raspadas** + **123 peças do CARF** (súmulas+acórdãos). ~15 mil trechos buscáveis.
- Embeddings via **Ollama nomic-embed** (local, grátis). Re-indexar: `python rag_local.py`.

## Banco de templates de contratos
- `templates/<familia>/template.md` + `wizard.json` (campos `{{}}` + módulos `[[]]`). Descoberta dinâmica.
- 4 famílias curadas (vesting, compra/venda imóvel, permuta, agrário) + ~66 gerados pelo modelo local.

## Ferramentas de bastidor (`tools/`)
- `ingest_contratos.py` — lê/mascara/organiza contratos do Drive.
- `gerar_templates.py` — gera templates via qwen2.5:14b local.
- `baixar_leis.py` / `processar_vademecum.py` — legislação para o RAG.
- `raspar_rfb.py` — raspagem do SIJUT2 via **Playwright** (navegador-robô, grátis).
- `processar_carf.py` — processa súmulas/acórdãos do CARF.

## Infra local
- **Streamlit** gerenciado por launchd `br.com.magusfiscal.streamlit`. Reiniciar: `launchctl kickstart -k gui/$(id -u)/br.com.magusfiscal.streamlit`.
- **Backup** diário do `usuarios.db` (launchd 03h).
- **Ollama** com `qwen2.5:14b` (geração), `llama3.2` (destilação), `nomic-embed` (busca).
- **OpenClaw** religado com modelo local (qwen2.5:14b), porta 18789.
- **Cloudflare Tunnel** (cloudflared) → magusfiscal.com.br.
- A versão antiga na nuvem (Streamlit Cloud) está **fechada** (Sharing restrito).

## ⚠️ Regras operacionais
- **NÃO reiniciar o app durante horário de uso sem avisar** (reinício = ~10s fora; um cadastro já se perdeu assim).
- **16 GB de RAM é o gargalo**: rodar processamento pesado só em horário tranquilo, com `nice -19` e `ollama stop qwen2.5:14b` para liberar memória.
- Demo: **usar dados fictícios**.

## Pendências / próximos passos
- Validar **juridicamente** as regras do `diagnostico_engine.py` (Jefferson).
- Plataforma: calculadora de prazos + agenda; IA sobre os dados; integração Google/Microsoft Calendar.
- Curadoria dos ~66 templates gerados; ~51 contratos faltantes (lote interrompido).
- Cecília: cadastro perdido na instabilidade — refazer ou cadastrar manualmente.
