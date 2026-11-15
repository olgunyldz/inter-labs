# S02 — NetworkPolicy whitelisting
on_exit kb -n "$SHOP_NS" delete networkpolicy --all
on_exit kb -n "$SHOP_NS" delete deploy probe-impostor --wait=false
probe_pod probe-impostor "$SHOP_NS" rogue gateway
kb apply -f policies/netpol.yaml >/dev/null
sleep 20
n_chain=$(chain_ok probe-gateway && echo ok || echo bozuk); n_e2e=$(e2e_ok && echo ok || echo bozuk)
n_ready=$(shop_all_ready && echo ok || echo bozuk)
metric naive.chain_ok "$([ $n_chain = ok ] && echo 1 || echo 0)" bool "standart kurallarla zincir çalışıyor"
metric naive.e2e_ok "$([ $n_e2e = ok ] && echo 1 || echo 0)" bool
metric naive.pods_ready "$([ $n_ready = ok ] && echo 1 || echo 0)" bool "standart kurallarla pod'lar sağlıklı (probe'lar geçiyor)"
if [ -f "policies/mesh-aware-$MESH.yaml" ]; then
  [ "$n_chain$n_e2e$n_ready" != okokok ] && finding "Standart NetworkPolicy seti $MESH ile uyumsuz (zincir=$n_chain, uçtan uca=$n_e2e, pod sağlığı=$n_ready). Mesh'e özel ek kural gerekiyor: $(grep -m1 '^#' "policies/mesh-aware-$MESH.yaml" | sed 's/^# //')"
  kb apply -f "policies/mesh-aware-$MESH.yaml" >/dev/null
  metric mesh_specific_rules "$(grep -c '^kind: NetworkPolicy' "policies/mesh-aware-$MESH.yaml")" adet "mesh için gereken ek NetworkPolicy"
  sleep 20
else
  metric mesh_specific_rules 0 adet
  [ "$n_chain$n_e2e$n_ready" != okokok ] && finding "Standart NetworkPolicy seti $MESH ile uyumsuz (zincir=$n_chain, uçtan uca=$n_e2e, pod sağlığı=$n_ready)."
fi
check_true "zincir çalışıyor (8 servis)" chain_ok probe-gateway
check_true "uçtan uca erişim (edge -> ingress -> gateway)" e2e_ok
check_true "tüm shop pod'ları sağlıklı" shop_all_ready
expect_access "gateway rolü -> order"          izin probe-gateway "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "yetkisiz pod -> order"          ret  probe-rogue   "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "yetkisiz pod -> catalog"        ret  probe-rogue   "$SHOP_NS" "http://catalog.$SHOP_NS.svc:9090/"
expect_access "başka namespace -> order"       ret  probe-outside "$OUTSIDE_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "yatay geçiş: gateway -> catalog" ret probe-gateway "$SHOP_NS" "http://catalog.$SHOP_NS.svc:9090/"
c=$(http_code probe-impostor "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/")
metric impostor_access "$(is_2xx "$c" && echo 1 || echo 0)" bool "etiketi taklit eden pod order'a erişebildi mi"
is_2xx "$c" && finding "NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP $c). Kimlik bazlı kural için mesh yetki politikası gerekir (S03)."
true
