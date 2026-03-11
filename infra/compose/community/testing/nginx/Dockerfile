FROM nginx:1.25-alpine

# Install inotify-tools
RUN apk add --no-cache inotify-tools

RUN mkdir -p /opt/community_frontend

COPY ./conf.d/default.conf /etc/nginx/conf.d/default.conf

# Copy the certificate watch script
COPY watch_certs.sh /usr/local/bin/watch_certs.sh
RUN chmod +x /usr/local/bin/watch_certs.sh

# Set the entrypoint to the watch script
ENTRYPOINT ["/usr/local/bin/watch_certs.sh"]

