"""
auth.py — Módulo de autenticação e gestão de usuários MAGUS Fiscal
Banco de dados: SQLite local (usuarios.db)
"""
import os
import hashlib
import secrets
import string
import sqlite3
from datetime import datetime
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "usuarios.db")

# ── Banco de dados ────────────────────────────────────────────────────────────

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def _init_db():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nome          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            telefone      TEXT,
            senha_hash    TEXT,
            status        TEXT    DEFAULT 'pendente',
            perfil        TEXT    DEFAULT 'avaliador',
            data_cadastro TEXT,
            req_total     INTEGER DEFAULT 0,
            ultimo_acesso TEXT,
            obs           TEXT
        )""")
        # Migração: adiciona coluna telefone se não existir (banco já criado)
        try:
            c.execute("ALTER TABLE usuarios ADD COLUMN telefone TEXT")
            c.commit()
        except Exception:
            pass  # coluna já existe
        c.commit()

_init_db()

# ── Utilitários ───────────────────────────────────────────────────────────────

def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()

def _gerar_senha() -> str:
    """Gera senha legível de 10 chars: 4 letras maiúsculas + 2 números + 4 letras minúsculas."""
    letras_mai = string.ascii_uppercase
    letras_min = string.ascii_lowercase
    nums       = string.digits
    partes = (
        [secrets.choice(letras_mai) for _ in range(3)] +
        [secrets.choice(nums)       for _ in range(2)] +
        [secrets.choice(letras_min) for _ in range(3)]
    )
    secrets.SystemRandom().shuffle(partes)
    return "".join(partes)

def _agora() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ── CRUD de usuários ──────────────────────────────────────────────────────────

def cadastrar_usuario(nome: str, email: str, telefone: str, perfil: str) -> dict:
    """Registra novo usuário com status pendente."""
    email = email.strip().lower()
    try:
        with _conn() as c:
            c.execute(
                "INSERT INTO usuarios (nome, email, telefone, perfil, data_cadastro) VALUES (?,?,?,?,?)",
                (nome.strip(), email, telefone.strip(), perfil, _agora())
            )
            c.commit()
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
    with _conn() as c:
        c.execute("UPDATE usuarios SET req_total = req_total + 1 WHERE id=?", (user_id,))
        c.commit()

def listar_usuarios() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, nome, email, telefone, status, perfil, data_cadastro, req_total, ultimo_acesso, obs "
            "FROM usuarios ORDER BY status, data_cadastro DESC"
        ).fetchall()
    return [{"id":r[0],"nome":r[1],"email":r[2],"telefone":r[3],"status":r[4],"perfil":r[5],
             "cadastro":r[6],"req":r[7],"ultimo":r[8],"obs":r[9]} for r in rows]

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
    """Gera nova senha e reativa usuário."""
    return aprovar_usuario(user_id)

def excluir_usuario(user_id: int):
    with _conn() as c:
        c.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        c.commit()

def atualizar_obs(user_id: int, obs: str):
    with _conn() as c:
        c.execute("UPDATE usuarios SET obs=? WHERE id=?", (obs, user_id))
        c.commit()

# ── CSS extra para as telas de auth ──────────────────────────────────────────

CSS_AUTH = """
<style>
/* ─ Abas de login ─ */
.auth-tabs { display:flex; gap:.5rem; margin-bottom:1.5rem; }
.auth-tab-ativo   { background:rgba(200,151,58,.12); border:1px solid rgba(200,151,58,.4);
                    color:#c8973a; border-radius:8px; padding:.4rem 1rem;
                    font-size:.78rem; font-weight:700; cursor:default; }
.auth-tab-inativo { background:transparent; border:1px solid #1a1f35;
                    color:#35405a; border-radius:8px; padding:.4rem 1rem;
                    font-size:.78rem; cursor:pointer; }
/* ─ Card de aprovação ─ */
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
/* ─ Tabela admin ─ */
.usr-row { display:flex; align-items:center; gap:.5rem; padding:.5rem .6rem;
           border-bottom:1px solid #0d1020; font-size:.82rem; }
.usr-row:hover { background:rgba(200,151,58,.03); }
.badge-ativo     { background:rgba(42,180,85,.15); color:#48c870;
                   border-radius:20px; padding:.1rem .55rem; font-size:.68rem; font-weight:700; }
.badge-pendente  { background:rgba(200,151,58,.12); color:#c8973a;
                   border-radius:20px; padding:.1rem .55rem; font-size:.68rem; font-weight:700; }
.badge-bloqueado { background:rgba(180,40,40,.15); color:#e06060;
                   border-radius:20px; padding:.1rem .55rem; font-size:.68rem; font-weight:700; }
</style>
"""

# ── Tela de login + cadastro ──────────────────────────────────────────────────

def tela_login():
    """
    Exibe login/cadastro. Seta st.session_state.usuario se bem-sucedido.
    Sempre termina com st.stop().
    """
    st.markdown(CSS_AUTH, unsafe_allow_html=True)
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown("""
        <div class="login-head">
          <h1>⚖️ MAGUS Fiscal</h1>
          <p>Plataforma de IA Tributária · Acesso Restrito</p>
        </div>
        """, unsafe_allow_html=True)

        aba = st.radio("", ["🔑  Entrar", "📝  Solicitar Acesso"],
                       horizontal=True, label_visibility="collapsed",
                       key="auth_aba")

        st.markdown('<div class="login-box">', unsafe_allow_html=True)

        # ── ABA: ENTRAR ────────────────────────────────────
        if aba == "🔑  Entrar":
            email = st.text_input("E-mail", placeholder="seu@email.com",
                                  label_visibility="collapsed", key="li_email")
            senha = st.text_input("Senha", type="password",
                                  placeholder="🔑  Sua senha de acesso",
                                  label_visibility="collapsed", key="li_senha")
            entrar = st.button("Entrar  →", type="primary",
                               use_container_width=True, key="btn_entrar")

            if entrar and email and senha:
                # Admin direto — lê .env com strip para evitar caracteres invisíveis
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
                        # Verifica se existe mas está pendente
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

        # ── ABA: SOLICITAR ACESSO ──────────────────────────
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

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="login-nota">
          MAGUS.IA · Acesso restrito a avaliadores autorizados<br>
          Dúvidas: juridico@magus.ia.br
        </div>""", unsafe_allow_html=True)

    st.stop()


# ── Painel Admin ──────────────────────────────────────────────────────────────

def painel_admin():
    """Renderiza painel completo de gestão de usuários (apenas para admin)."""
    st.markdown(CSS_AUTH, unsafe_allow_html=True)
    st.markdown("## 👤 Gestão de Usuários")

    usuarios = listar_usuarios()
    pendentes  = [u for u in usuarios if u["status"] == "pendente"]
    ativos     = [u for u in usuarios if u["status"] == "ativo"]
    bloqueados = [u for u in usuarios if u["status"] == "bloqueado"]

    # ── Métricas rápidas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total cadastros", len(usuarios))
    c2.metric("⏳ Pendentes", len(pendentes))
    c3.metric("✅ Ativos", len(ativos))
    c4.metric("🚫 Bloqueados", len(bloqueados))

    st.divider()

    # ── PENDENTES primeiro (ação necessária)
    if pendentes:
        st.markdown(f"### ⏳ Pendentes de aprovação ({len(pendentes)})")
        for u in pendentes:
            tel = u.get("telefone") or ""
            tel_limpo = "".join(c for c in tel if c.isdigit())
            wa_link = f"https://wa.me/55{tel_limpo}" if tel_limpo else ""
            wa_badge = f' · <a href="{wa_link}" target="_blank" style="color:#25d366;font-size:.75rem;">📲 WhatsApp</a>' if wa_link else ""
            with st.expander(f"📩 {u['nome']} — {u['email']} · {u['perfil']} · {u['cadastro']}"):
                st.markdown(f"**Telefone:** {tel or '—'}{wa_badge}", unsafe_allow_html=True)
                obs = st.text_input("Observação (opcional)", value=u['obs'] or "",
                                    key=f"obs_{u['id']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Aprovar e gerar senha", key=f"ap_{u['id']}", type="primary"):
                        nova = aprovar_usuario(u['id'], obs)
                        st.session_state[f"senha_gerada_{u['id']}"] = nova
                        st.rerun()
                with col2:
                    if st.button("🗑️ Recusar e excluir", key=f"ex_{u['id']}"):
                        excluir_usuario(u['id'])
                        st.rerun()

                if f"senha_gerada_{u['id']}" in st.session_state:
                    senha_mostrar = st.session_state[f"senha_gerada_{u['id']}"]
                    st.markdown(f"""
                    <div class="senha-card">
                      <h4>✅ Usuário aprovado! Envie esta senha:</h4>
                      <div class="senha-gerada">{senha_mostrar}</div>
                      <p style="color:#6a9a7a;font-size:.8rem;margin:.4rem 0 0">
                        Copie e envie por WhatsApp/e-mail para <b>{u['email']}</b>
                      </p>
                    </div>
                    """, unsafe_allow_html=True)

    # ── ATIVOS
    if ativos:
        st.markdown(f"### ✅ Usuários ativos ({len(ativos)})")
        for u in ativos:
            tel = u.get("telefone") or ""
            tel_limpo = "".join(c for c in tel if c.isdigit())
            wa_link = f"https://wa.me/55{tel_limpo}" if tel_limpo else ""
            wa_badge = f' · <a href="{wa_link}" target="_blank" style="color:#25d366;font-size:.75rem;">📲 WhatsApp</a>' if wa_link else ""
            with st.expander(f"👤 {u['nome']} — {u['email']} · {u['req']} consultas · último: {u['ultimo'] or 'nunca'}"):
                st.markdown(f"**Telefone:** {tel or '—'}{wa_badge}", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔄 Nova senha", key=f"ns_{u['id']}"):
                        nova = reativar_usuario(u['id'])
                        st.session_state[f"senha_gerada_{u['id']}"] = nova
                        st.rerun()
                with col2:
                    if st.button("🚫 Bloquear", key=f"bl_{u['id']}"):
                        bloquear_usuario(u['id'])
                        st.rerun()
                with col3:
                    if st.button("🗑️ Excluir", key=f"del_{u['id']}"):
                        excluir_usuario(u['id'])
                        st.rerun()

                if f"senha_gerada_{u['id']}" in st.session_state:
                    senha_mostrar = st.session_state[f"senha_gerada_{u['id']}"]
                    st.markdown(f"""
                    <div class="senha-card">
                      <h4>🔄 Nova senha gerada:</h4>
                      <div class="senha-gerada">{senha_mostrar}</div>
                      <p style="color:#6a9a7a;font-size:.8rem;margin:.4rem 0 0">
                        Envie para <b>{u['email']}</b>
                      </p>
                    </div>
                    """, unsafe_allow_html=True)

                obs_nova = st.text_input("Obs", value=u['obs'] or "",
                                         key=f"obs2_{u['id']}", label_visibility="collapsed",
                                         placeholder="Observações sobre este usuário...")
                if st.button("💾 Salvar obs", key=f"sv_{u['id']}"):
                    atualizar_obs(u['id'], obs_nova)
                    st.success("Salvo!")

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
                        st.rerun()
                with col2:
                    if st.button("🗑️ Excluir", key=f"del2_{u['id']}"):
                        excluir_usuario(u['id'])
                        st.rerun()

                if f"senha_gerada_{u['id']}" in st.session_state:
                    senha_mostrar = st.session_state[f"senha_gerada_{u['id']}"]
                    st.markdown(f"""
                    <div class="senha-card">
                      <h4>✅ Reativado! Nova senha:</h4>
                      <div class="senha-gerada">{senha_mostrar}</div>
                    </div>
                    """, unsafe_allow_html=True)

    if not usuarios:
        st.info("Nenhum usuário cadastrado ainda.")
