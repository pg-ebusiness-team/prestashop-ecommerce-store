FROM nginx:alpine

RUN apk add --no-cache openssl

COPY templates/ /etc/nginx/templates/
COPY docker-entrypoint.d/05-generate-cert.sh /docker-entrypoint.d/05-generate-cert.sh
RUN chmod +x /docker-entrypoint.d/05-generate-cert.sh