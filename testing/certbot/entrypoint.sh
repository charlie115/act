#!/bin/sh

email=ckddjs116@gmail.com
domain=my-test.orbitholdings.org

# Check and generate options-ssl-nginx.conf
if [ ! -f /etc/letsencrypt/options-ssl-nginx.conf ]; then
    echo "Generating options-ssl-nginx.conf..."
    wget -O /etc/letsencrypt/options-ssl-nginx.conf \
        https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf
fi

# Check and generate ssl-dhparams.pem
if [ ! -f /etc/letsencrypt/ssl-dhparams.pem ]; then
    echo "Generating ssl-dhparams.pem..."
    openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048
fi

# Check if certificates exist
if [ ! -f /etc/letsencrypt/live/$domain/fullchain.pem ]; then
    echo "Certificates not found, generating certificates..."
    certbot certonly --webroot --webroot-path=/var/www/certbot \
        --email $email --agree-tos --no-eff-email \
        -d $domain
else
    echo "Certificates already exist."
fi

# Start the renewal process
exec "$@"