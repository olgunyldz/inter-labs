# S03 — Kimlik bazlı yetki
on_exit authz_clear
on_exit kb -n "$SHOP_NS" delete deploy probe-impostor --wait=false
probe_pod probe-impostor "$SHOP_NS" rogue gateway
authz_render "$MESH" > "$(raw policy.yaml)"
kb apply -f "$(raw policy.yaml)" >/dev/null
metric policy_objects "$(grep -c '^kind:' "$(raw policy.yaml)")" adet "uygulanan politika nesnesi sayısı"
sleep 15
check_true "zincir çalışıyor (8 servis, tüm kenarlar yetkili)" chain_ok probe-gateway
check_true "uçtan uca erişim (ingress kimliği yetkili)" e2e_ok
check_true "tüm shop pod'ları sağlıklı" shop_all_ready
expect_access "gateway kimliği -> order"        izin probe-gateway  "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "rogue kimliği -> order"          ret  probe-rogue    "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "rogue kimliği -> gateway"        ret  probe-rogue    "$SHOP_NS" "http://gateway.$SHOP_NS.svc:9090/"
expect_access "yatay geçiş: gateway -> catalog" ret  probe-gateway  "$SHOP_NS" "http://catalog.$SHOP_NS.svc:9090/"
expect_access "kimlik taklidi (etiket=gateway, sa=rogue) -> order" ret probe-impostor "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "mesh dışı namespace -> order"    ret  probe-outside  "$OUTSIDE_NS" "http://order.$SHOP_NS.svc:9090/"
c=$(http_code probe-rogue "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/")
metric deny_http_code "$c" kod "reddedilen isteğin cevabı (403 = L7 ret, 000 = bağlantı reddi)"
