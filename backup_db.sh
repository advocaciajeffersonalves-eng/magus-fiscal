#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  backup_db.sh — Cópia de segurança automática do banco de usuários
#                 do MAGUS Fiscal.
#
#  O que faz: copia o usuarios.db para a pasta backups/ com a data e hora
#  no nome, e mantém apenas as 30 cópias mais recentes (apaga as antigas
#  sozinho, pra não lotar o disco).
#
#  Roda sozinho via agendador do Mac (launchd), 1x por dia.
#  Você também pode rodar na mão a qualquer momento:  bash backup_db.sh
# ─────────────────────────────────────────────────────────────────────
set -e

DIR="/Users/jeffersonalves/magus-fiscal"
ORIGEM="$DIR/usuarios.db"
DEST="$DIR/backups"
MANTER=30

mkdir -p "$DEST"

if [ ! -f "$ORIGEM" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S')  ERRO: usuarios.db nao encontrado" >> "$DEST/backup.log"
    exit 1
fi

STAMP=$(date +%Y-%m-%d_%Hh%M)
cp "$ORIGEM" "$DEST/usuarios_$STAMP.db"

# rotação: mantém só as $MANTER cópias mais recentes
ls -1t "$DEST"/usuarios_*.db 2>/dev/null | tail -n +$((MANTER + 1)) | while read -r velho; do
    rm -f "$velho"
done

echo "$(date '+%Y-%m-%d %H:%M:%S')  backup ok -> usuarios_$STAMP.db" >> "$DEST/backup.log"
