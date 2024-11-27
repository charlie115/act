#!/bin/sh

# Variables
domain="my-test.orbitholdings.org"

# Start the certificate watcher in the background
(
  while inotifywait -e modify,create,delete /etc/letsencrypt/live/$domain/; do
    echo "Certificate change detected, reloading Nginx..."
    nginx -s reload
  done
) &

# Start Nginx in the foreground
nginx -g 'daemon off;'