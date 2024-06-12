ui = true
api_addr = "https://<addr goes here>:8200"

storage "file" {
    path = "/vault/file"
}

listener "tcp" {
    address       = "0.0.0.0:8200"
    tls_cert_file = "/vault.crt"
    tls_key_file  = "/vault.key"
}
