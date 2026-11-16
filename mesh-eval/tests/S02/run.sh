# S02 — NetworkPolicy whitelisting
on_exit kb -n "$SHOP_NS" delete networkpolicy --all
on_exit kb -n "$SHOP_NS" delete deploy probe-impostor --wait=false
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
[ "$MESH" = istio-ambient-l7 ] && finding "istio-ambient-l7: servisler arası tüm trafik waypoint üzerinden geldiği için hedef pod'daki NetworkPolicy yalnızca waypoint'i kaynak olarak görür; waypoint'e izin vermek zorunlu olduğundan çağıran bazlı NetworkPolicy kuralları (ör. yalnızca gateway -> order) etkisiz kalır. Bu profilde servisler arası erişim kontrolü yalnızca mesh yetki politikasıyla (S03) yapılabilir."
expect_access "yetkisiz pod -> order"          ret  probe-rogue   "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/"
rc=$(http_code probe-rogue "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/")
is_2xx "$rc" && finding "$MESH: NetworkPolicy order'a yalnızca gateway rolüne izin verdiği halde yetkisiz pod (rogue) order'a erişebildi (HTTP $rc). Mesh proxy'si başka iş yüklerinin açtığı bağlantıları paylaştığında NetworkPolicy bağlantının gerçek kaynağını göremiyor; davranış aralıklı."
expect_access "yetkisiz pod -> catalog"        ret  probe-rogue   "$SHOP_NS" "http://catalog.$SHOP_NS.svc:9090/"
expect_access "başka namespace -> order"       ret  probe-outside "$OUTSIDE_NS" "http://order.$SHOP_NS.svc:9090/"
expect_access "yatay geçiş: gateway -> catalog" ret probe-gateway "$SHOP_NS" "http://catalog.$SHOP_NS.svc:9090/"
# (4) Etiket taklidi: etiketi gateway, kimliği (SA) rogue olan pod
probe_pod probe-impostor "$SHOP_NS" rogue gateway
c=$(http_code probe-impostor "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/")
metric impostor_access "$(is_2xx "$c" && echo 1 || echo 0)" bool "etiketi taklit eden pod order'a erişebildi mi"
is_2xx "$c" && finding "NetworkPolicy etiket bazlıdır: shop.role=gateway etiketini taşıyan farklı kimlikli bir pod order'a erişebildi (HTTP $c). Kimlik bazlı kural için mesh yetki politikası gerekir (S03)."
# (5) Ortak kimlik: izinli bir pod (impostor) ile aynı SA'yı paylaşan yetkisiz pod (rogue) kuralı aşabiliyor mu?
#     (ambient: ztunnel aynı kimliğin trafiğini ortak HBONE bağlantısından taşıyabilir; NetworkPolicy IP'ye bakar)
ok_n=$(kb -n "$SHOP_NS" exec deploy/probe-rogue -c probe -- bash -c \
  "for i in \$(seq 20); do curl -s -o /dev/null -w '%{http_code}\n' --max-time 2 http://order.$SHOP_NS.svc:9090/; done" 2>/dev/null | grep -c '^2' || true)
metric shared_identity_bypass "$ok_n" "/20" "aynı SA'yı paylaşan izinli pod bağlıyken yetkisiz pod'un geçen isteği"
check "ortak kimlik üzerinden NetworkPolicy atlatılamıyor (20 deneme)" 0 "$ok_n"
[ "$ok_n" -gt 0 ] && finding "$MESH: yetkisiz pod (rogue), NetworkPolicy'nin izin verdiği ve aynı ServiceAccount'u paylaşan başka bir pod order'a bağlıyken 20 isteğin $ok_n tanesinde kuralı aştı. Mesh proxy'si aynı kimliğin trafiğini ortak bağlantı üzerinden taşıyor; NetworkPolicy yalnızca bağlantının kaynağını (IP) görüyor. Bu mesh'te NetworkPolicy tek başına güvenilir bir sınır değil; kimlik bazlı mesh kuralı (S03) gerekir."
true
