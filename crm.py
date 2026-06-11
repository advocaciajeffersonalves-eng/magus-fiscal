"""
CRM — Ficha de cliente e histórico de serviços (MAGUS Fiscal).

Cada profissional logado (advogado/contador) cadastra seus clientes e acompanha
o histórico de serviços/documentos de cada um. Tabelas novas no mesmo usuarios.db
(não tocam na tabela de usuários existente). Demo: usar dados fictícios.
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "usuarios.db")


def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_crm():
    """Cria as tabelas de clientes e histórico se ainda não existirem."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                profissional  INTEGER NOT NULL,
                nome          TEXT NOT NULL,
                documento     TEXT,
                email         TEXT,
                telefone      TEXT,
                tipo          TEXT,
                obs           TEXT,
                criado_em     TEXT DEFAULT (datetime('now','localtime'))
            )""")
        c.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id  INTEGER NOT NULL,
                tipo        TEXT,
                titulo      TEXT,
                detalhe     TEXT,
                criado_em   TEXT DEFAULT (datetime('now','localtime'))
            )""")
        c.commit()


def criar_cliente(profissional, nome, documento="", email="", telefone="", tipo="PF", obs=""):
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO clientes (profissional,nome,documento,email,telefone,tipo,obs) "
            "VALUES (?,?,?,?,?,?,?)",
            (profissional, nome.strip(), documento.strip(), email.strip(),
             telefone.strip(), tipo, obs.strip()))
        c.commit()
        return cur.lastrowid


def listar_clientes(profissional):
    with _conn() as c:
        return [dict(id=r[0], nome=r[1], documento=r[2], email=r[3], telefone=r[4],
                     tipo=r[5], obs=r[6], criado_em=r[7], n_servicos=r[8])
                for r in c.execute("""
                    SELECT cl.id, cl.nome, cl.documento, cl.email, cl.telefone, cl.tipo,
                           cl.obs, cl.criado_em,
                           (SELECT COUNT(*) FROM historico h WHERE h.cliente_id=cl.id)
                    FROM clientes cl WHERE cl.profissional=? ORDER BY cl.nome
                """, (profissional,))]


def cliente(cliente_id):
    with _conn() as c:
        r = c.execute("SELECT id,nome,documento,email,telefone,tipo,obs FROM clientes WHERE id=?",
                      (cliente_id,)).fetchone()
    return dict(id=r[0], nome=r[1], documento=r[2], email=r[3], telefone=r[4],
                tipo=r[5], obs=r[6]) if r else None


def registrar_servico(cliente_id, tipo, titulo, detalhe=""):
    """Vincula um serviço/documento (diagnóstico, defesa, contrato...) ao cliente."""
    with _conn() as c:
        c.execute("INSERT INTO historico (cliente_id,tipo,titulo,detalhe) VALUES (?,?,?,?)",
                  (cliente_id, tipo, titulo.strip(), detalhe.strip()))
        c.commit()


def historico(cliente_id):
    with _conn() as c:
        return [dict(id=r[0], tipo=r[1], titulo=r[2], detalhe=r[3], criado_em=r[4])
                for r in c.execute(
                    "SELECT id,tipo,titulo,detalhe,criado_em FROM historico "
                    "WHERE cliente_id=? ORDER BY id DESC", (cliente_id,))]


def excluir_cliente(cliente_id):
    with _conn() as c:
        c.execute("DELETE FROM historico WHERE cliente_id=?", (cliente_id,))
        c.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        c.commit()
