#!/bin/sh
# Sandi akun latihan dari env (default hanya untuk demo lokal; port terikat 127.0.0.1).
echo "latihan:${SSH_DEMO_PASSWORD:-latihan123}" | chpasswd
mkdir -p /var/log/waspada
# sshd -e menulis pesan polos ke stderr; diberi awalan format syslog ("Nov  4 09:15:31 host sshd[pid]: ...")
# agar sama persis dengan /var/log/auth.log server Linux biasa, format yang dibaca parser auth WASPADA.
/usr/sbin/sshd -D -e 2>&1 | while IFS= read -r line; do
  printf '%s %s sshd[%s]: %s\n' "$(date '+%b %e %H:%M:%S')" "$(hostname)" "$$" "$line"
done >> /var/log/waspada/auth.log
