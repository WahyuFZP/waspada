FROM alpine:3.20
RUN apk add --no-cache openssh-server && ssh-keygen -A && adduser -D -s /bin/sh latihan
COPY sshd_config /etc/ssh/sshd_config
COPY entrypoint.sh /entrypoint.sh
CMD ["/bin/sh", "/entrypoint.sh"]
