# Mesh CLI'ları: sürüm başına .tools/ altına indirilir (host'taki kurulumlardan bağımsız)
#   .tools/istio-<sürüm>/  (istioctl + helm chart'ları)   .tools/linkerd-<sürüm>

istio_dir() { echo "$TOOLS/istio-$1"; }
istioctl_v() { "$(istio_dir "$1")/bin/istioctl" "${@:2}"; }
linkerd_bin() { echo "$TOOLS/linkerd-$1"; }

fetch_istio() {
  local v=$1 d
  d=$(istio_dir "$v")
  [ -x "$d/bin/istioctl" ] && return
  log "Istio $v indiriliyor"
  curl -fsSL "https://github.com/istio/istio/releases/download/$v/istio-$v-linux-amd64.tar.gz" | tar xz -C "$TOOLS"
  ok "$d"
}

fetch_linkerd() {
  local v=$1 b
  b=$(linkerd_bin "$v")
  [ -x "$b" ] && return
  log "Linkerd $v indiriliyor"
  curl -fsSL -o "$b" "https://github.com/linkerd/linkerd2/releases/download/$v/linkerd2-cli-$v-linux-amd64"
  chmod +x "$b"
  ok "$b"
}

tools_install() {
  fetch_istio "$ISTIO_VERSION"; fetch_istio "$ISTIO_PREV_VERSION"
  fetch_linkerd "$LINKERD_VERSION"; fetch_linkerd "$LINKERD_PREV_VERSION"
  istioctl_v "$ISTIO_VERSION" version --remote=false
  "$(linkerd_bin "$LINKERD_VERSION")" version --client
}
