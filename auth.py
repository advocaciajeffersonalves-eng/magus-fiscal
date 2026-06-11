"""
auth.py — Módulo de autenticação e gestão de usuários MAGUS Fiscal
Banco de dados: SQLite local (usuarios.db)
"""
import os
import ssl
import time
import hashlib
import secrets
import string
import sqlite3
import smtplib
import urllib.request
import urllib.parse
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "usuarios.db")

LIMITE_DIA = 5
LIMITE_MES = 20

# ── Banco de dados ────────────────────────────────────────────────────────────

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def _init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nome            TEXT    NOT NULL,
            email           TEXT    UNIQUE NOT NULL,
            telefone        TEXT,
            senha_hash      TEXT,
            status          TEXT    DEFAULT 'pendente',
            perfil          TEXT    DEFAULT 'avaliador',
            data_cadastro   TEXT,
            req_total       INTEGER DEFAULT 0,
            ultimo_acesso   TEXT,
            obs             TEXT,
            consultas_hoje  INTEGER DEFAULT 0,
            data_hoje       TEXT    DEFAULT '',
            consultas_mes   INTEGER DEFAULT 0,
            mes_atual       TEXT    DEFAULT ''
        )""")

        c.execute("""
        CREATE TABLE IF NOT EXISTS historico_consultas (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            data_hora TEXT    NOT NULL,
            modulo    TEXT    DEFAULT '',
            tipo      TEXT    DEFAULT '',
            status    TEXT    DEFAULT 'ok',
            erro      TEXT    DEFAULT '',
            tempo_ms  INTEGER DEFAULT 0
        )""")

        # Migrações seguras — ignoram se coluna já existe
        for col_sql in [
            "ALTER TABLE usuarios ADD COLUMN telefone TEXT",
            "ALTER TABLE usuarios ADD COLUMN consultas_hoje INTEGER DEFAULT 0",
            "ALTER TABLE usuarios ADD COLUMN data_hoje TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN consultas_mes INTEGER DEFAULT 0",
            "ALTER TABLE usuarios ADD COLUMN mes_atual TEXT DEFAULT ''",
        ]:
            try:
                c.execute(col_sql)
                c.commit()
            except Exception:
                pass
        c.commit()

_init_db()

# ── Utilitários ───────────────────────────────────────────────────────────────

def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def _gerar_senha() -> str:
    """Gera senha legível de 8 chars."""
    partes = (
        [secrets.choice(string.ascii_uppercase) for _ in range(3)] +
        [secrets.choice(string.digits)          for _ in range(2)] +
        [secrets.choice(string.ascii_lowercase) for _ in range(3)]
    )
    secrets.SystemRandom().shuffle(partes)
    return "".join(partes)

def _agora() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def _hoje_str() -> str:
    return date.today().isoformat()

def _mes_str() -> str:
    return datetime.now().strftime("%Y-%m")

# ── Telegram Bot ─────────────────────────────────────────────────────────────

def enviar_telegram(mensagem: str) -> dict:
    """Envia mensagem ao admin via Telegram Bot. Configurar TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no .env."""
    token   = os.getenv("TELEGRAM_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return {"ok": False, "erro": "TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID não configurados no .env"}
    try:
        params = urllib.parse.urlencode({"chat_id": chat_id, "text": mensagem, "parse_mode": "Markdown"})
        url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
        with urllib.request.urlopen(url, timeout=8) as r:
            r.read()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "erro": str(e)}

# ── Envio de e-mail de acesso ─────────────────────────────────────────────────

def enviar_email_acesso(nome: str, email_destino: str, senha: str) -> dict:
    """Envia e-mail de boas-vindas com senha ao usuário aprovado."""
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    if not gmail_user or not gmail_pass:
        return {"ok": False, "erro": "Credenciais de e-mail não configuradas no .env"}

    assunto = "✅ Seu acesso ao MAGUS Fiscal foi aprovado"
    corpo_html = f"""
    <div style="font-family:Arial,sans-serif;max-width:540px;margin:0 auto;background:#0a0a0f;color:#e8e8f0;border-radius:12px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#1a1428,#0e0c1a);padding:2rem;text-align:center;border-bottom:2px solid #c8973a;">
        <h1 style="color:#c8973a;margin:0;font-size:1.8rem;">⚖️ MAGUS Fiscal</h1>
        <p style="color:#888;margin:.5rem 0 0;font-size:.9rem;">Plataforma de IA Tributária</p>
      </div>
      <div style="padding:2rem;">
        <p style="font-size:1rem;">Olá, <strong>{nome}</strong>!</p>
        <p style="color:#aaa;">Seu acesso foi <strong style="color:#48c870;">aprovado</strong>. Use as credenciais abaixo:</p>
        <div style="background:#0e1117;border:1px solid #c8973a;border-radius:8px;padding:1.2rem;margin:1.5rem 0;text-align:center;">
          <p style="color:#888;font-size:.8rem;margin:0 0 .4rem;">🔗 Endereço de acesso</p>
          <a href="https://magusfiscal.com.br" style="color:#c8973a;font-size:1.1rem;font-weight:700;text-decoration:none;">magusfiscal.com.br</a>
        </div>
        <div style="background:#0e1117;border:1px solid rgba(200,151,58,.3);border-radius:8px;padding:1.2rem;margin:1rem 0;">
          <p style="color:#888;font-size:.8rem;margin:0 0 .3rem;">📧 E-mail de acesso</p>
          <p style="font-family:monospace;font-size:1rem;margin:0;color:#e8e8f0;">{email_destino}</p>
        </div>
        <div style="background:#0e1117;border:1px solid rgba(72,200,112,.4);border-radius:8px;padding:1.2rem;margin:1rem 0;text-align:center;">
          <p style="color:#888;font-size:.8rem;margin:0 0 .3rem;">🔑 Senha de acesso</p>
          <p style="font-family:monospace;font-size:1.6rem;font-weight:800;letter-spacing:.15em;color:#f0e0c0;margin:0;">{senha}</p>
        </div>
        <p style="color:#888;font-size:.85rem;margin-top:1.5rem;">
          ⚠️ <strong>Guarde esta senha</strong> — ela não é armazenada em texto visível.<br>
          Se precisar de nova senha, entre em contato com a equipe MAGUS.
        </p>
        <div style="margin-top:1.5rem;text-align:center;">
          <a href="https://magusfiscal.com.br" style="background:linear-gradient(135deg,#c8973a,#e6b85c);color:#0a0a0f;padding:.8rem 2rem;border-radius:8px;font-weight:700;text-decoration:none;font-size:1rem;">
            → Acessar agora
          </a>
        </div>
      </div>
      <div style="padding:1rem 2rem;text-align:center;border-top:1px solid #1a1f35;">
        <p style="color:#444;font-size:.75rem;margin:0;">
          MAGUS.IA Tecnologia · juridico@magus.ia.br<br>
          Este é um e-mail automático — não responda diretamente.
        </p>
      </div>
    </div>
    """
    reply_to     = os.getenv("GMAIL_REPLY_TO", gmail_user).strip()
    from_name    = os.getenv("GMAIL_FROM_NAME", "MAGUS Fiscal").strip()
    from_address = os.getenv("GMAIL_FROM_ADDRESS", gmail_user).strip()
    try:
        msg = MIMEMultipart("alternative")
        msg["From"]     = f"{from_name} <{from_address}>"
        msg["To"]       = email_destino
        msg["Subject"]  = assunto
        msg["Reply-To"] = reply_to
        msg.attach(MIMEText(corpo_html, "html", "utf-8"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as srv:
            srv.login(gmail_user, gmail_pass)
            srv.sendmail(gmail_user, email_destino, msg.as_string())
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "erro": str(e)}

# ── Controle de limites e histórico de consultas ──────────────────────────────

def verificar_limite(user_id: int) -> dict:
    """Verifica se o usuário pode fazer mais uma consulta (5/dia, 20/mês)."""
    hoje = _hoje_str()
    mes  = _mes_str()
    with _conn() as c:
        row = c.execute(
            "SELECT consultas_hoje, data_hoje, consultas_mes, mes_atual FROM usuarios WHERE id=?",
            (user_id,)
        ).fetchone()
    if not row:
        return {"ok": False, "motivo": "Usuário não encontrado."}
    c_hoje, d_hoje, c_mes, m_atual = row
    if d_hoje != hoje:
        c_hoje = 0
    if m_atual != mes:
        c_mes = 0
    if c_hoje >= LIMITE_DIA:
        return {"ok": False, "motivo": f"Limite diário atingido ({LIMITE_DIA} consultas/dia). Aguarde amanhã ou solicite liberação."}
    if c_mes >= LIMITE_MES:
        return {"ok": False, "motivo": f"Limite mensal atingido ({LIMITE_MES} consultas/mês). Entre em contato com a equipe MAGUS."}
    return {"ok": True, "dia": c_hoje, "mes": c_mes}

def registrar_consulta(user_id: int, modulo: str, tipo: str, status: str, erro: str = "", tempo_ms: int = 0):
    """Registra consulta no histórico e atualiza contadores. Envia alerta WhatsApp se limite diário atingido."""
    hoje = _hoje_str()
    mes  = _mes_str()
    with _conn() as c:
        c.execute(
            "INSERT INTO historico_consultas (user_id, data_hora, modulo, tipo, status, erro, tempo_ms) VALUES (?,?,?,?,?,?,?)",
            (user_id, _agora(), modulo, tipo, status, erro, tempo_ms)
        )
        row = c.execute(
            "SELECT consultas_hoje, data_hoje, consultas_mes, mes_atual FROM usuarios WHERE id=?",
            (user_id,)
        ).fetchone()
        if row:
            c_hoje, d_hoje, c_mes, m_atual = row
            novo_c_hoje = (c_hoje + 1) if d_hoje == hoje else 1
            novo_c_mes  = (c_mes  + 1) if m_atual == mes  else 1
            c.execute(
                "UPDATE usuarios SET req_total=req_total+1, consultas_hoje=?, data_hoje=?, "
                "consultas_mes=?, mes_atual=?, ultimo_acesso=? WHERE id=?",
                (novo_c_hoje, hoje, novo_c_mes, mes, _agora(), user_id)
            )
        c.commit()

    # Alerta WhatsApp quando bate o limite diário
    if status == "ok":
        with _conn() as c:
            row2 = c.execute(
                "SELECT nome, email, consultas_hoje, consultas_mes FROM usuarios WHERE id=?",
                (user_id,)
            ).fetchone()
        if row2:
            nome_u, email_u, c_hoje_novo, c_mes_novo = row2
            if c_hoje_novo >= LIMITE_DIA:
                enviar_telegram(
                    f"⚠️ MAGUS Fiscal — Limite diário atingido\n"
                    f"Usuário: *{nome_u}* ({email_u})\n"
                    f"Consultas hoje: {c_hoje_novo}/{LIMITE_DIA} | Mês: {c_mes_novo}/{LIMITE_MES}\n"
                    f"Acesse o painel admin para liberar quota extra se necessário."
                )

def liberar_quota_extra(user_id: int):
    """Zera o contador diário do usuário (liberação de acesso extra pelo admin)."""
    with _conn() as c:
        c.execute("UPDATE usuarios SET consultas_hoje=0, data_hoje='' WHERE id=?", (user_id,))
        c.commit()

def listar_historico_usuario(user_id: int, limite: int = 20) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, data_hora, modulo, tipo, status, erro, tempo_ms "
            "FROM historico_consultas WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limite)
        ).fetchall()
    return [{"id":r[0],"data_hora":r[1],"modulo":r[2],"tipo":r[3],
             "status":r[4],"erro":r[5],"tempo_ms":r[6]} for r in rows]

# ── CRUD de usuários ──────────────────────────────────────────────────────────

def cadastrar_usuario(nome: str, email: str, telefone: str, perfil: str) -> dict:
    """Registra novo usuário com status pendente e notifica admin via WhatsApp."""
    email = email.strip().lower()
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO usuarios (nome, email, telefone, perfil, data_cadastro) VALUES (?,?,?,?,?)",
                (nome.strip(), email, telefone.strip(), perfil, _agora())
            )
            c.commit()
        enviar_telegram(
            f"📩 *Novo cadastro MAGUS Fiscal*\n"
            f"Nome: {nome.strip()}\n"
            f"E-mail: {email}\n"
            f"Telefone: {telefone.strip() or '—'}\n"
            f"Perfil: {perfil}\n"
            f"Acesse o painel admin para aprovar."
        )
        return {"ok": True}
    except sqlite3.IntegrityError:
        return {"ok": False, "erro": "Este e-mail já está cadastrado."}

def login(email: str, senha: str) -> dict | None:
    """Retorna dict do usuário se login válido, None caso contrário."""
    email = email.strip().lower()
    with _conn() as c:
        row = c.execute(
            "SELECT id, nome, email, senha_hash, status, perfil, req_total FROM usuarios WHERE email=?",
            (email,)
        ).fetchone()
    if not row:
        return None
    uid, nome, em, hash_salvo, status, perfil, req = row
    if status != "ativo":
        return None
    if hash_salvo and _hash(senha) == hash_salvo:
        with _conn() as c:
            c.execute("UPDATE usuarios SET ultimo_acesso=? WHERE id=?", (_agora(), uid))
            c.commit()
        return {"id": uid, "nome": nome, "email": em, "status": status,
                "perfil": perfil, "req_total": req}
    return None

def incrementar_uso(user_id: int):
    """Compatibilidade legada — prefira registrar_consulta() para novos fluxos."""
    with _conn() as c:
        c.execute("UPDATE usuarios SET req_total = req_total + 1 WHERE id=?", (user_id,))
        c.commit()

def trocar_senha(user_id: int, senha_atual: str, nova_senha: str) -> dict:
    """Permite ao usuário trocar sua própria senha."""
    with _conn() as c:
        row = c.execute("SELECT senha_hash FROM usuarios WHERE id=?", (user_id,)).fetchone()
    if not row:
        return {"ok": False, "erro": "Usuário não encontrado."}
    if row[0] != _hash(senha_atual):
        return {"ok": False, "erro": "Senha atual incorreta."}
    if len(nova_senha) < 6:
        return {"ok": False, "erro": "Nova senha deve ter pelo menos 6 caracteres."}
    with _conn() as c:
        c.execute("UPDATE usuarios SET senha_hash=? WHERE id=?", (_hash(nova_senha), user_id))
        c.commit()
    return {"ok": True}

def listar_usuarios() -> list[dict]:
    hoje = _hoje_str()
    mes  = _mes_str()
    with _conn() as c:
        rows = c.execute(
            "SELECT id, nome, email, telefone, status, perfil, data_cadastro, req_total, ultimo_acesso, obs, "
            "consultas_hoje, data_hoje, consultas_mes, mes_atual "
            "FROM usuarios ORDER BY status, data_cadastro DESC"
        ).fetchall()
    result = []
    for r in rows:
        c_hoje = r[10] if r[11] == hoje else 0
        c_mes  = r[12] if r[13] == mes  else 0
        result.append({
            "id":r[0],"nome":r[1],"email":r[2],"telefone":r[3],"status":r[4],"perfil":r[5],
            "cadastro":r[6],"req":r[7],"ultimo":r[8],"obs":r[9],
            "hoje":c_hoje,"mes":c_mes
        })
    return result

def aprovar_usuario(user_id: int, obs: str = "") -> str:
    """Aprova usuário e retorna a senha gerada."""
    nova_senha = _gerar_senha()
    with _conn() as c:
        c.execute(
            "UPDATE usuarios SET status='ativo', senha_hash=?, obs=? WHERE id=?",
            (_hash(nova_senha), obs, user_id)
        )
        c.commit()
    return nova_senha

def bloquear_usuario(user_id: int):
    with _conn() as c:
        c.execute("UPDATE usuarios SET status='bloqueado' WHERE id=?", (user_id,))
        c.commit()

def reativar_usuario(user_id: int) -> str:
    return aprovar_usuario(user_id)

def excluir_usuario(user_id: int):
    with _conn() as c:
        c.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        c.commit()

def atualizar_obs(user_id: int, obs: str):
    with _conn() as c:
        c.execute("UPDATE usuarios SET obs=? WHERE id=?", (obs, user_id))
        c.commit()

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS_AUTH = """
<style>
@keyframes magus-run {
  from { stroke-dashoffset: 0; }
  to   { stroke-dashoffset: -1000; }
}
@keyframes magus-glow-bg {
  0%,100% { opacity: 0.10; }
  50%     { opacity: 0.20; }
}
@keyframes magus-ant {
  0%,100% { stroke: rgba(201,161,74,0.14); }
  50%     { stroke: #fde488; }
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Fundo animado ── */
.login-bg-wrap {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 0;
    pointer-events: none;
    animation: magus-glow-bg 3.4s ease-in-out infinite;
}

/* ── Header do login ── */
.login-head {
    text-align: center;
    padding: 2rem 0 1.4rem;
    animation: fadeInUp 0.5s ease-out;
    position: relative;
    z-index: 1;
}
.login-title {
    background: linear-gradient(135deg, #c8973a 0%, #f0c060 50%, #c88030 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.1rem;
    font-weight: 900;
    letter-spacing: 0.06em;
    line-height: 1.1;
    margin: 0.6rem 0 0.4rem;
}
.login-subtitle {
    color: rgba(255, 255, 255, 0.75);
    font-size: 0.68rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
}
.login-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(200,151,58,0.35), transparent);
    margin: 1rem 0 1.4rem;
}

/* ── Card da coluna central ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {
    background: rgba(7, 9, 15, 0.72) !important;
    border: 1px solid rgba(200, 151, 58, 0.16);
    border-radius: 20px;
    box-shadow: 0 24px 60px rgba(0,0,0,0.55), inset 0 1px 0 rgba(200,151,58,0.07);
    animation: fadeInUp 0.5s ease-out;
    position: relative;
    z-index: 1;
}

/* ── Esconde barra de dev do Streamlit ── */
header[data-testid="stHeader"]    { display: none !important; }
[data-testid="stStatusWidget"]    { display: none !important; }
#MainMenu                          { display: none !important; }

/* ── Campos de input ── */
input[type="text"],
input[type="password"],
input[type="email"],
input:not([type]) {
    background: rgba(22, 28, 50, 0.95) !important;
    border: 1px solid rgba(200, 151, 58, 0.50) !important;
    color: #f0ece0 !important;
    font-size: 0.95rem !important;
    border-radius: 8px !important;
}
input::placeholder {
    color: rgba(200, 185, 145, 0.80) !important;
}
input:focus {
    border-color: #c8973a !important;
    box-shadow: 0 0 0 2px rgba(200, 151, 58, 0.20) !important;
    background: rgba(28, 35, 60, 0.98) !important;
}

/* ── Rodapé ── */
.login-nota {
    text-align: center;
    color: #252a3a;
    font-size: 0.7rem;
    margin-top: 1rem;
    line-height: 1.8;
}

/* ── Admin / painel ── */
.senha-card {
    background:linear-gradient(135deg,rgba(8,22,14,.95),rgba(5,16,10,.98));
    border:1px solid rgba(42,180,85,.5); border-radius:10px;
    padding:1rem 1.4rem; margin:.8rem 0;
}
.senha-card h4 { color:#48c870; margin:0 0 .4rem; font-size:.9rem; }
.senha-gerada  { font-family:monospace; font-size:1.4rem; font-weight:800;
                 color:#f0e0c0; letter-spacing:.12em; background:rgba(200,151,58,.08);
                 border:1px solid rgba(200,151,58,.2); border-radius:6px;
                 padding:.4rem .8rem; display:inline-block; margin:.3rem 0; }
.usr-row { display:flex; align-items:center; gap:.5rem; padding:.5rem .6rem;
           border-bottom:1px solid #0d1020; font-size:.82rem; }
.usr-row:hover { background:rgba(200,151,58,.03); }
.badge-ativo     { background:rgba(42,180,85,.15); color:#48c870;
                   border-radius:20px; padding:.1rem .55rem; font-size:.68rem; font-weight:700; }
.badge-pendente  { background:rgba(200,151,58,.12); color:#c8973a;
                   border-radius:20px; padding:.1rem .55rem; font-size:.68rem; font-weight:700; }
.badge-bloqueado { background:rgba(180,40,40,.15); color:#e06060;
                   border-radius:20px; padding:.1rem .55rem; font-size:.68rem; font-weight:700; }
.quota-wrap { display:flex; gap:1.2rem; margin:.5rem 0 .8rem; }
.quota-item { text-align:center; }
.quota-num  { font-size:1.3rem; font-weight:800; line-height:1; }
.quota-sub  { font-size:.68rem; color:#555; margin-top:.1rem; }
.quota-ok   { color:#48c870; }
.quota-warn { color:#c8973a; }
.quota-full { color:#e06060; }
.hist-row { display:grid; grid-template-columns:7rem 5rem 6rem 1fr; gap:.5rem;
            padding:.3rem .5rem; border-bottom:1px solid #0a0d18; font-size:.73rem; }
.hist-header { color:#35405a; font-weight:700; font-size:.68rem; }
.hist-ok   { color:#48c870; font-weight:700; }
.hist-erro { color:#e06060; font-weight:700; }
.hist-ms   { color:#35405a; }
</style>
"""

# ── Tela de login + cadastro ──────────────────────────────────────────────────

def tela_login():
    """Exibe login/cadastro. Seta st.session_state.usuario se bem-sucedido."""
    st.markdown(CSS_AUTH, unsafe_allow_html=True)

    # Símbolo MAGUS animado ao fundo (fixo, grande, baixa opacidade)
    st.markdown("""
    <div class="login-bg-wrap">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="640" height="640">
        <g transform="translate(256,256)">
          <path d="M -130,0 C -130,-60 -38,-60 0,0 C 38,60 130,60 130,0 C 130,-60 38,-60 0,0 C -38,60 -130,60 -130,0"
            fill="none" stroke="rgba(201,161,74,0.18)" stroke-width="22" stroke-linecap="round"/>
          <path d="M -130,0 C -130,-60 -38,-60 0,0 C 38,60 130,60 130,0 C 130,-60 38,-60 0,0 C -38,60 -130,60 -130,0"
            fill="none" stroke="#c8973a" stroke-width="18" stroke-linecap="round"
            pathLength="1000" stroke-dasharray="110 890"
            style="animation: magus-run 2.8s linear infinite; filter: drop-shadow(0 0 14px rgba(200,151,58,0.9));"/>
          <line x1="158" y1="-20" x2="158" y2="20" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"
            style="animation: magus-ant 1.3s ease-in-out infinite;"/>
          <line x1="184" y1="-11" x2="184" y2="11" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"
            style="animation: magus-ant 1.3s ease-in-out infinite; animation-delay:0.42s;"/>
        </g>
      </svg>
    </div>
    """, unsafe_allow_html=True)

    _, c, _ = st.columns([1, 2, 1])
    with c:
        # Header com logo animado menor
        st.markdown("""
        <div class="login-head">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="160" height="160"
               style="display:block; margin:0 auto; filter:drop-shadow(0 0 24px rgba(200,151,58,0.55));">
            <g transform="translate(256,256)">
              <path d="M -130,0 C -130,-60 -38,-60 0,0 C 38,60 130,60 130,0 C 130,-60 38,-60 0,0 C -38,60 -130,60 -130,0"
                fill="none" stroke="rgba(201,161,74,0.28)" stroke-width="22" stroke-linecap="round"/>
              <path d="M -130,0 C -130,-60 -38,-60 0,0 C 38,60 130,60 130,0 C 130,-60 38,-60 0,0 C -38,60 -130,60 -130,0"
                fill="none" stroke="#fde488" stroke-width="22" stroke-linecap="round"
                pathLength="1000" stroke-dasharray="110 890"
                style="animation: magus-run 2.8s linear infinite; filter: drop-shadow(0 0 7px #f0c84a);"/>
              <line x1="158" y1="-20" x2="158" y2="20" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"
                style="animation: magus-ant 1.3s ease-in-out infinite;"/>
              <line x1="184" y1="-11" x2="184" y2="11" stroke="#C9A14A" stroke-width="22" stroke-linecap="round"
                style="animation: magus-ant 1.3s ease-in-out infinite; animation-delay:0.42s;"/>
            </g>
          </svg>
          <div class="login-title">MAGUS Fiscal</div>
          <div class="login-subtitle">Plataforma de IA Tributária · Acesso Restrito</div>
          <div class="login-divider"></div>
        </div>
        """, unsafe_allow_html=True)

        aba = st.radio("", ["🔑  Entrar", "📝  Solicitar Acesso"],
                       horizontal=True, label_visibility="collapsed",
                       key="auth_aba")

        # ── ABA: ENTRAR
        if aba == "🔑  Entrar":
            email = st.text_input("E-mail", placeholder="seu@email.com",
                                  label_visibility="collapsed", key="li_email")
            senha = st.text_input("Senha", type="password",
                                  placeholder="🔑  Sua senha de acesso",
                                  label_visibility="collapsed", key="li_senha")
            entrar = st.button("Entrar  →", type="primary",
                               use_container_width=True, key="btn_entrar")

            if entrar and email and senha:
                admin_email = os.getenv("ADMIN_EMAIL", "admin@magus.ia").strip()
                admin_senha = os.getenv("ADMIN_SENHA", "adminmagus2026").strip()
                eh_admin = (email.strip().lower() == admin_email.lower()
                            and senha.strip() == admin_senha)

                if eh_admin:
                    st.session_state.usuario = {
                        "id": 0, "nome": "Jefferson (Admin)", "email": admin_email,
                        "perfil": "admin", "req_total": 0
                    }
                    st.session_state.autenticado = True
                    st.rerun()
                else:
                    usuario = login(email, senha)
                    if usuario:
                        st.session_state.usuario = usuario
                        st.session_state.autenticado = True
                        st.rerun()
                    else:
                        with _conn() as conn:
                            row = conn.execute(
                                "SELECT status FROM usuarios WHERE email=?",
                                (email.strip().lower(),)
                            ).fetchone()
                        if row and row[0] == "pendente":
                            st.warning("⏳ Cadastro aguardando aprovação. Você receberá a senha por e-mail.")
                        elif row and row[0] == "bloqueado":
                            st.error("🚫 Acesso bloqueado. Entre em contato com a equipe MAGUS.")
                        else:
                            st.error("E-mail ou senha incorretos.")

        # ── ABA: SOLICITAR ACESSO
        else:
            nome = st.text_input("Nome completo", placeholder="Seu nome completo",
                                 label_visibility="collapsed", key="ca_nome")
            email = st.text_input("E-mail", placeholder="seu@email.com",
                                  label_visibility="collapsed", key="ca_email")
            telefone = st.text_input("WhatsApp / Telefone", placeholder="(62) 99999-9999",
                                     label_visibility="collapsed", key="ca_tel")
            perfil = st.selectbox("Seu perfil", [
                "Advogado(a) Tributarista",
                "Contador(a) / Contabilista",
                "Empresário(a) / Gestor(a)",
                "Investidor(a)",
                "Outro"
            ], label_visibility="collapsed", key="ca_perfil")
            solicitar = st.button("Solicitar Acesso", type="primary",
                                  use_container_width=True, key="btn_solicitar")

            if solicitar:
                if not nome or not email:
                    st.warning("Preencha nome e e-mail.")
                elif "@" not in email:
                    st.warning("E-mail inválido.")
                else:
                    res = cadastrar_usuario(nome, email, telefone, perfil)
                    if res["ok"]:
                        st.success("✅ Solicitação enviada! A equipe MAGUS analisará e enviará sua senha em breve.")
                    else:
                        st.warning(res["erro"])

        st.markdown("""
        <div class="login-nota">
          MAGUS.IA · Acesso restrito a avaliadores autorizados<br>
          Dúvidas: juridico@magus.ia.br
        </div>""", unsafe_allow_html=True)

    st.stop()


# ── Tela de troca de senha (chamada do app.py) ────────────────────────────────

def tela_troca_senha(user_id: int):
    """Renderiza formulário de troca de senha para o usuário logado."""
    st.markdown(CSS_AUTH, unsafe_allow_html=True)
    st.markdown("### 🔑 Alterar Senha")
    with st.form("form_troca_senha"):
        atual = st.text_input("Senha atual", type="password", key="ts_atual")
        nova  = st.text_input("Nova senha (mín. 6 caracteres)", type="password", key="ts_nova")
        conf  = st.text_input("Confirmar nova senha", type="password", key="ts_conf")
        salvar = st.form_submit_button("Salvar nova senha", type="primary")
    if salvar:
        if not atual or not nova or not conf:
            st.warning("Preencha todos os campos.")
        elif nova != conf:
            st.error("As senhas não coincidem.")
        else:
            res = trocar_senha(user_id, atual, nova)
            if res["ok"]:
                st.success("✅ Senha alterada com sucesso!")
            else:
                st.error(res["erro"])


# ── Painel Admin ──────────────────────────────────────────────────────────────

def _badge_quota(valor: int, limite: int) -> str:
    pct  = valor / limite if limite else 0
    cor  = "quota-ok" if pct < 0.6 else ("quota-warn" if pct < 1.0 else "quota-full")
    return f'<span class="quota-num {cor}">{valor}</span><div class="quota-sub">/{limite}</div>'

def painel_admin():
    """Renderiza painel completo de gestão de usuários (apenas para admin)."""
    st.markdown(CSS_AUTH, unsafe_allow_html=True)
    st.markdown("## 👤 Gestão de Usuários")

    usuarios = listar_usuarios()
    pendentes  = [u for u in usuarios if u["status"] == "pendente"]
    ativos     = [u for u in usuarios if u["status"] == "ativo"]
    bloqueados = [u for u in usuarios if u["status"] == "bloqueado"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total cadastros", len(usuarios))
    c2.metric("⏳ Pendentes", len(pendentes))
    c3.metric("✅ Ativos", len(ativos))
    c4.metric("🚫 Bloqueados", len(bloqueados))

    st.divider()

    # ── PENDENTES
    if pendentes:
        st.markdown(f"### ⏳ Pendentes de aprovação ({len(pendentes)})")
        for u in pendentes:
            tel = u.get("telefone") or ""
            tel_limpo = "".join(ch for ch in tel if ch.isdigit())
            wa_link  = f"https://wa.me/55{tel_limpo}" if tel_limpo else ""
            wa_badge = f' · <a href="{wa_link}" target="_blank" style="color:#25d366;font-size:.75rem;">📲 WhatsApp</a>' if wa_link else ""
            with st.expander(f"📩 {u['nome']} — {u['email']} · {u['perfil']} · {u['cadastro']}"):
                st.markdown(f"**Telefone:** {tel or '—'}{wa_badge}", unsafe_allow_html=True)
                obs = st.text_input("Observação (opcional)", value=u['obs'] or "", key=f"obs_{u['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Aprovar e enviar acesso", key=f"ap_{u['id']}", type="primary"):
                        nova = aprovar_usuario(u['id'], obs)
                        st.session_state[f"senha_gerada_{u['id']}"] = nova
                        resultado_email = enviar_email_acesso(u['nome'], u['email'], nova)
                        st.session_state[f"email_status_{u['id']}"] = resultado_email
                        st.rerun()
                with col2:
                    if st.button("🗑️ Recusar e excluir", key=f"ex_{u['id']}"):
                        excluir_usuario(u['id'])
                        st.rerun()

                if f"senha_gerada_{u['id']}" in st.session_state:
                    senha_mostrar = st.session_state[f"senha_gerada_{u['id']}"]
                    email_res = st.session_state.get(f"email_status_{u['id']}", {})
                    if email_res.get("ok"):
                        email_info = f'<p style="color:#48c870;font-size:.82rem;margin:.6rem 0 0">📧 <b>E-mail enviado</b> para <b>{u["email"]}</b></p>'
                    elif email_res.get("erro"):
                        email_info = f'<p style="color:#e09040;font-size:.8rem;margin:.6rem 0 0">⚠️ E-mail não enviado ({email_res["erro"]}). Envie a senha manualmente.</p>'
                    else:
                        email_info = f'<p style="color:#6a9a7a;font-size:.8rem;margin:.4rem 0 0">Envie por WhatsApp/e-mail para <b>{u["email"]}</b></p>'
                    st.markdown(f"""
                    <div class="senha-card">
                      <h4>✅ Usuário aprovado!</h4>
                      <div class="senha-gerada">{senha_mostrar}</div>
                      {email_info}
                    </div>
                    """, unsafe_allow_html=True)

    # ── ATIVOS
    if ativos:
        st.markdown(f"### ✅ Usuários ativos ({len(ativos)})")
        for u in ativos:
            tel = u.get("telefone") or ""
            tel_limpo = "".join(ch for ch in tel if ch.isdigit())
            wa_link  = f"https://wa.me/55{tel_limpo}" if tel_limpo else ""
            wa_badge = f' · <a href="{wa_link}" target="_blank" style="color:#25d366;font-size:.75rem;">📲 WhatsApp</a>' if wa_link else ""
            hoje_n = u["hoje"]
            mes_n  = u["mes"]
            with st.expander(
                f"👤 {u['nome']} — {u['email']} · {u['req']} consultas · "
                f"hoje: {hoje_n}/{LIMITE_DIA} · mês: {mes_n}/{LIMITE_MES} · "
                f"último: {u['ultimo'] or 'nunca'}"
            ):
                st.markdown(f"**Telefone:** {tel or '—'}{wa_badge}", unsafe_allow_html=True)

                # Quotas visuais
                pct_dia = min(hoje_n / LIMITE_DIA, 1.0)
                pct_mes = min(mes_n  / LIMITE_MES,  1.0)
                st.markdown(f"""
                <div class="quota-wrap">
                  <div class="quota-item">
                    {_badge_quota(hoje_n, LIMITE_DIA)}
                    <div style="font-size:.7rem;color:#666;margin-top:.2rem;">hoje</div>
                  </div>
                  <div class="quota-item">
                    {_badge_quota(mes_n, LIMITE_MES)}
                    <div style="font-size:.7rem;color:#666;margin-top:.2rem;">este mês</div>
                  </div>
                  <div class="quota-item">
                    <span class="quota-num" style="color:#c8973a;">{u['req']}</span>
                    <div class="quota-sub">total</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    if st.button("🔄 Nova senha", key=f"ns_{u['id']}"):
                        nova = reativar_usuario(u['id'])
                        st.session_state[f"senha_gerada_{u['id']}"] = nova
                        resultado_email = enviar_email_acesso(u['nome'], u['email'], nova)
                        st.session_state[f"email_status_{u['id']}"] = resultado_email
                        st.rerun()
                with col2:
                    if st.button("➕ Liberar quota", key=f"lq_{u['id']}"):
                        liberar_quota_extra(u['id'])
                        st.success("Quota diária liberada!")
                        st.rerun()
                with col3:
                    if st.button("🚫 Bloquear", key=f"bl_{u['id']}"):
                        bloquear_usuario(u['id'])
                        st.rerun()
                with col4:
                    if st.button("🗑️ Excluir", key=f"del_{u['id']}"):
                        excluir_usuario(u['id'])
                        st.rerun()

                if f"senha_gerada_{u['id']}" in st.session_state:
                    senha_mostrar = st.session_state[f"senha_gerada_{u['id']}"]
                    email_res = st.session_state.get(f"email_status_{u['id']}", {})
                    if email_res.get("ok"):
                        email_info = f'<p style="color:#48c870;font-size:.82rem;margin:.6rem 0 0">📧 <b>E-mail enviado</b> para <b>{u["email"]}</b></p>'
                    elif email_res.get("erro"):
                        email_info = f'<p style="color:#e09040;font-size:.8rem;margin:.6rem 0 0">⚠️ E-mail não enviado ({email_res["erro"]}). Envie manualmente.</p>'
                    else:
                        email_info = f'<p style="color:#6a9a7a;font-size:.8rem;margin:.4rem 0 0">Envie para <b>{u["email"]}</b></p>'
                    st.markdown(f"""
                    <div class="senha-card">
                      <h4>🔄 Nova senha gerada:</h4>
                      <div class="senha-gerada">{senha_mostrar}</div>
                      {email_info}
                    </div>
                    """, unsafe_allow_html=True)

                obs_nova = st.text_input("Obs", value=u['obs'] or "",
                                         key=f"obs2_{u['id']}", label_visibility="collapsed",
                                         placeholder="Observações sobre este usuário...")
                if st.button("💾 Salvar obs", key=f"sv_{u['id']}"):
                    atualizar_obs(u['id'], obs_nova)
                    st.success("Salvo!")

                # Histórico de consultas
                historico = listar_historico_usuario(u['id'])
                if historico:
                    st.markdown("**📋 Últimas consultas:**")
                    st.markdown("""
                    <div class="hist-row hist-header">
                      <span>Data/Hora</span><span>Status</span><span>Módulo</span><span>Tipo / Erro</span>
                    </div>
                    """, unsafe_allow_html=True)
                    for h in historico:
                        st_class = "hist-ok" if h["status"] == "ok" else "hist-erro"
                        st_label = "✅ ok" if h["status"] == "ok" else f"❌ erro"
                        detalhe  = h["erro"] if h["status"] != "ok" and h["erro"] else h["tipo"]
                        ms_label = f'{h["tempo_ms"]}ms' if h["tempo_ms"] else "—"
                        st.markdown(f"""
                        <div class="hist-row">
                          <span style="color:#555">{h["data_hora"]}</span>
                          <span class="{st_class}">{st_label}</span>
                          <span style="color:#8899aa">{h["modulo"] or "—"}</span>
                          <span style="color:#aaa">{detalhe or "—"} <span class="hist-ms">{ms_label}</span></span>
                        </div>
                        """, unsafe_allow_html=True)

    # ── BLOQUEADOS
    if bloqueados:
        st.markdown(f"### 🚫 Bloqueados ({len(bloqueados)})")
        for u in bloqueados:
            with st.expander(f"🚫 {u['nome']} — {u['email']}"):
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Reativar", key=f"re_{u['id']}", type="primary"):
                        nova = reativar_usuario(u['id'])
                        st.session_state[f"senha_gerada_{u['id']}"] = nova
                        resultado_email = enviar_email_acesso(u['nome'], u['email'], nova)
                        st.session_state[f"email_status_{u['id']}"] = resultado_email
                        st.rerun()
                with col2:
                    if st.button("🗑️ Excluir", key=f"del2_{u['id']}"):
                        excluir_usuario(u['id'])
                        st.rerun()

                if f"senha_gerada_{u['id']}" in st.session_state:
                    senha_mostrar = st.session_state[f"senha_gerada_{u['id']}"]
                    email_res = st.session_state.get(f"email_status_{u['id']}", {})
                    if email_res.get("ok"):
                        email_info = f'<p style="color:#48c870;font-size:.82rem;margin:.6rem 0 0">📧 <b>E-mail enviado</b> para <b>{u["email"]}</b></p>'
                    elif email_res.get("erro"):
                        email_info = f'<p style="color:#e09040;font-size:.8rem;margin:.6rem 0 0">⚠️ E-mail não enviado ({email_res["erro"]}). Envie manualmente.</p>'
                    else:
                        email_info = ""
                    st.markdown(f"""
                    <div class="senha-card">
                      <h4>✅ Reativado! Nova senha:</h4>
                      <div class="senha-gerada">{senha_mostrar}</div>
                      {email_info}
                    </div>
                    """, unsafe_allow_html=True)

    if not usuarios:
        st.info("Nenhum usuário cadastrado ainda.")
