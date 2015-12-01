STACK_OF(X509_NAME) *ca_names;
STACK_OF(SSL_CIPHER) **skp;
STACK_OF(SSL_CIPHER) *ssl_get_ciphers_by_id(SSL *s);
STACK_OF(SSL_CIPHER) **ssl_get_ciphers_by_id(SSL *s);
