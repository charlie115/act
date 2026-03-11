#!/bin/sh

echo "Renewing certificates..."
certbot renew --webroot --webroot-path=/var/www/certbot