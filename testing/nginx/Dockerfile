FROM nginx:1.25-alpine

RUN mkdir -p /opt/community_frontend
# Change to downloading frontend build files
# COPY ./build /opt/community_frontend/build

COPY ./conf.d/default.conf /etc/nginx/conf.d/default.conf
COPY ./snippets/self-signed.conf /etc/nginx/snippets/self-signed.conf
COPY ./snippets/ssl-params.conf /etc/nginx/snippets/ssl-params.conf
