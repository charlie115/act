FROM certbot/certbot

COPY entrypoint.sh /entrypoint.sh
COPY renew_certificates.sh /renew_certificates.sh

RUN chmod +x /entrypoint.sh /renew_certificates.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/bin/sh", "-c", "trap exit TERM; while :; do /renew_certificates.sh; sleep 12h; done;"]