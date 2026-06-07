#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────
#  ver_usuarios.py — Leitor da base de usuários do MAGUS Fiscal
#
#  Para que serve: mostrar, de forma simples e legível, quem se cadastrou
#  na base — nome, email, telefone, status, quando entrou e quanto usou.
#
#  Como usar (no terminal, dentro da pasta magus-fiscal):
#       python3 ver_usuarios.py
#
#  Não altera nada. Só LÊ e mostra. Pode rodar quantas vezes quiser.
# ─────────────────────────────────────────────────────────────────────
import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usuarios.db")


def main():
    if not os.path.exists(DB):
        print("\n  Banco 'usuarios.db' não encontrado nesta pasta.\n")
        return

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT id, nome, email, telefone, status, perfil,
               data_cadastro, ultimo_acesso, req_total, consultas_mes
        FROM usuarios
        ORDER BY data_cadastro DESC
        """
    ).fetchall()
    con.close()

    total = len(rows)
    por_status = {}
    for r in rows:
        s = r["status"] or "—"
        por_status[s] = por_status.get(s, 0) + 1

    print()
    print("=" * 72)
    print(f"  BASE DE USUÁRIOS — MAGUS FISCAL          {total} cadastrado(s)")
    print("=" * 72)
    resumo = "   ".join(f"{k}: {v}" for k, v in por_status.items())
    print("  Por status:   " + (resumo or "—"))
    print("  (mais recentes primeiro)")
    print("=" * 72)

    for r in rows:
        print()
        print(f"  #{r['id']}  {r['nome']}    [ {r['status']} · {r['perfil']} ]")
        print(f"      email .......: {r['email']}")
        print(f"      telefone ....: {r['telefone'] or '—'}")
        print(f"      cadastro ....: {r['data_cadastro'] or '—'}")
        print(f"      último acesso: {r['ultimo_acesso'] or 'nunca acessou'}")
        print(f"      uso .........: {r['req_total'] or 0} consultas no total"
              f"  ·  {r['consultas_mes'] or 0} neste mês")

    print()
    print("=" * 72)
    print()


if __name__ == "__main__":
    main()
