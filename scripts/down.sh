#!/usr/bin/env bash
# Edge LB'yi, tüm cluster'ları ve zone network'lerini siler
source "$(dirname "$0")/lib.sh"

docker rm -f "$EDGE_LB" >/dev/null 2>&1 && ok "silindi: $EDGE_LB"
for c in "${CLUSTERS[@]}"; do
  if kind get clusters 2>/dev/null | grep -qx "$c"; then
    log "Siliniyor: $c"
    kind delete cluster --name "$c"
  fi
done
for n in "$NET_EDGE" "$NET_DMZ" "$NET_APP" "$NET_DATA" "$NET_MGMT"; do
  docker network rm "$n" >/dev/null 2>&1 && ok "network silindi: $n"
done
true
