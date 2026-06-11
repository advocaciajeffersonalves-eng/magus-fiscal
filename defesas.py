"""
Gerador de Defesas (piloto) — MAGUS Fiscal.

A pessoa cola o texto da autuação (auto de infração). O motor busca os fundamentos
legais relevantes no acervo LOCAL (RAG, grátis) e gera uma minuta de impugnação
administrativa estruturada via IA (Sonnet — custa só na geração).

⚠️ Gera RASCUNHO a ser revisado e assinado por advogado. Não peticiona sozinha.
"""
import os
import anthropic
import rag_local

SYSTEM = (
    "Você é advogado tributarista brasileiro experiente em contencioso administrativo. "
    "Com base no AUTO DE INFRAÇÃO e nos FUNDAMENTOS LEGAIS fornecidos, redija uma minuta "
    "de IMPUGNAÇÃO/defesa administrativa, estruturada nas seções: I – DA TEMPESTIVIDADE; "
    "II – DA SÍNTESE DA AUTUAÇÃO; III – DAS PRELIMINARES (decadência, nulidade, cerceamento "
    "de defesa — apenas se cabíveis); IV – DO MÉRITO (teses de defesa fundamentadas na "
    "legislação citada); V – DOS PEDIDOS. "
    "Regras: linguagem jurídica formal, impessoal; cite a legislação pertinente dos fundamentos; "
    "NÃO invente fatos — use [DADO A COMPLETAR] onde faltar informação do caso; não use emojis "
    "nem títulos em markdown (#); não afirme certeza de êxito. Comece direto pelo cabeçalho da peça."
)


def _client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def ler_imagem(image_bytes: bytes, nome: str = "documento.jpg") -> str:
    """Transcreve o texto de uma foto/imagem de documento (auto de infração) via
    IA de visão. Custa só quando usado (poucos centavos por imagem)."""
    import base64
    media = "image/png" if nome.lower().endswith(".png") else "image/jpeg"
    b64 = base64.b64encode(image_bytes).decode()
    resp = _client().messages.create(
        model="claude-sonnet-4-6", max_tokens=4000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
            {"type": "text", "text": "Transcreva fielmente TODO o texto deste documento "
             "(provável auto de infração / autuação fiscal). Retorne apenas o texto transcrito, "
             "preservando números de processo, valores, datas e enquadramentos legais, sem comentários."},
        ]}])
    return resp.content[0].text.strip()


def gerar_defesa(texto_autuacao: str, max_tokens: int = 8000) -> str:
    """Gera a minuta de impugnação. Busca embasamento no acervo local (grátis)
    e redige via Sonnet. Retorna o texto da peça."""
    # busca fundamentos legais relevantes ao teor da autuação (consulta os
    # primeiros trechos da autuação, onde costumam estar tributo/artigos/motivo)
    fundamentos = rag_local.contexto(texto_autuacao[:600], k=6)
    prompt = (
        f"AUTO DE INFRAÇÃO / AUTUAÇÃO:\n{texto_autuacao}\n"
        f"{fundamentos}\n\n"
        f"Redija a minuta de impugnação administrativa completa, conforme as instruções."
    )
    resp = _client().messages.create(
        model="claude-sonnet-4-6", max_tokens=max_tokens,
        system=SYSTEM, messages=[{"role": "user", "content": prompt}])
    return resp.content[0].text.strip()
