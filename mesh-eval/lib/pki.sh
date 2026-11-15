# Mesh kimlik altyapısı (PKI). Mesh'lerin kendi kendine CA üretmesi yerine bizim kök/ara
# sertifikalarımız verilir ("plug-in CA") -> prod'daki kurumsal CA (Vault) senaryosunun karşılığı.
#   Istio  : RSA kök + cluster ara CA (cacerts secret)
#   Linkerd: ECDSA P-256 güven çapası + issuer (Linkerd ECDSA ister)
PKI_DIR="$STATE_DIR/pki"

_ca_ext() { printf 'basicConstraints=critical,CA:TRUE%s\nkeyUsage=critical,keyCertSign,cRLSign\nsubjectKeyIdentifier=hash\n' "${1:-}"; }

# pki_root <ad> <rsa|ec>
pki_root() {
  local d="$PKI_DIR/$1"
  [ -f "$d/root-cert.pem" ] && return
  mkdir -p "$d"
  if [ "$2" = ec ]; then
    openssl ecparam -name prime256v1 -genkey -noout -out "$d/root-key.pem" 2>/dev/null
  else
    openssl genrsa -out "$d/root-key.pem" 4096 2>/dev/null
  fi
  openssl req -x509 -new -key "$d/root-key.pem" -sha256 -days 3650 \
    -subj "/O=mesh-eval/CN=$1 root CA" -extensions v3 \
    -config <(printf '[req]\ndistinguished_name=dn\n[dn]\n[v3]\n'; _ca_ext) -out "$d/root-cert.pem"
}

# pki_intermediate <root-ad> <ara-ad> <rsa|ec> <cn> [gün]
pki_intermediate() {
  local d="$PKI_DIR/$1" i="$PKI_DIR/$1/$2" days=${5:-730}
  mkdir -p "$i"
  if [ "$3" = ec ]; then
    openssl ecparam -name prime256v1 -genkey -noout -out "$i/ca-key.pem" 2>/dev/null
  else
    openssl genrsa -out "$i/ca-key.pem" 2048 2>/dev/null
  fi
  openssl req -new -key "$i/ca-key.pem" -subj "/O=mesh-eval/CN=$4" -out "$i/ca.csr"
  openssl x509 -req -in "$i/ca.csr" -CA "$d/root-cert.pem" -CAkey "$d/root-key.pem" -CAcreateserial \
    -sha256 -days "$days" -extfile <(_ca_ext ',pathlen:0') -out "$i/ca-cert.pem" 2>/dev/null
  cat "$i/ca-cert.pem" "$d/root-cert.pem" > "$i/cert-chain.pem"
  cp "$d/root-cert.pem" "$i/root-cert.pem"
}

pki_istio() { # -> $PKI_DIR/istio/<ad>
  local name=${1:-cluster-a}
  pki_root istio rsa
  [ -f "$PKI_DIR/istio/$name/ca-cert.pem" ] || pki_intermediate istio "$name" rsa "istio intermediate $name"
  echo "$PKI_DIR/istio/$name"
}

pki_linkerd() { # -> $PKI_DIR/linkerd/<ad>
  local name=${1:-issuer}
  pki_root linkerd ec
  [ -f "$PKI_DIR/linkerd/$name/ca-cert.pem" ] || pki_intermediate linkerd "$name" ec identity.linkerd.cluster.local 365
  echo "$PKI_DIR/linkerd/$name"
}
