#!/bin/sh

# Variables
domain="acw-test.orbitholdings.org"
cert_dir="/etc/letsencrypt/live/$domain"

if [ -d "$cert_dir" ]; then
  (
    while inotifywait -e modify,create,delete "$cert_dir"/; do
      echo "Certificate change detected, reloading Nginx..."
      nginx -s reload
    done
  ) &
fi

# Start Nginx in the foreground
nginx -g 'daemon off;'
