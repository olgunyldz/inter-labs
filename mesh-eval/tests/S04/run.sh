# S04 — Endpoint bazlı L7 yetki
on_exit authz_clear
O="http://order.$SHOP_NS.svc:9090"
kb apply -f "policies/$MESH.yaml" >/dev/null
sleep 20
ready=$(shop_all_ready && echo 1 || echo 0)
metric probes_ok_without_fix "$ready" bool "kural tek başına uygulanınca pod'lar sağlıklı mı"
if [ "$ready" = 0 ] && [ -f "policies/$MESH-probes.yaml" ]; then
  finding "$MESH: endpoint kuralı tek başına kubelet sağlık kontrollerini (/ready) engelledi; order pod'ları NotReady oldu. Probe yolları için ek kural gerekiyor (policies/$MESH-probes.yaml)."
  kb apply -f "policies/$MESH-probes.yaml" >/dev/null
  sleep 20
fi
# Yayılma: kural tüm proxy'lere ulaşana kadar bekle (ardışık 10 ret), süreyi kaydet. Sabit bekleme
# yerine yakınsama: tek bir proxy'nin geç güncellenmesi kural hatası değil, yayılma gecikmesidir.
if [ "$MESH" != istio-ambient ]; then
  t0=$SECONDS; streak=0
  while [ $((SECONDS - t0)) -lt 120 ] && [ "$streak" -lt 10 ]; do
    if [ "$(http_code probe-gateway "$SHOP_NS" "$O/admin")" != 200 ]; then streak=$((streak + 1)); else streak=0; sleep 1; fi
  done
  conv=$(( SECONDS - t0 + 20 ))
  metric converge_s "$conv" sn "kural uygulandıktan sonra tüm proxy'lerde tutarlı ret (yaklaşık, 20 sn ilk bekleme dahil)"
  [ "$conv" -gt 25 ] && finding "$MESH: L7 kuralın tüm proxy'lerde tutarlı uygulanması yaklaşık $conv sn sürdü; bu süre boyunca bazı istekler yasak endpoint'e ulaşabildi."
fi
if [ "$MESH" = istio-ambient ]; then
  # waypoint'siz L4 modu: ztunnel HTTP özniteliklerini göremez
  codes=""
  for u in "/" "/api/orders" "/admin"; do codes+="GET$u=$(http_code probe-gateway "$SHOP_NS" "$O$u") "; done
  codes+="POST/=$(http_code probe-gateway "$SHOP_NS" "$O/" -X POST)"
  echo "$codes" > "$(raw observed.txt)"
  finding "Ambient L4 (waypoint'siz): path/method içeren kural ztunnel'de uygulanamaz. Gözlenen: $codes (zincir: $(chain_ok probe-gateway && echo çalışıyor || echo bozuk)). L7 kural için waypoint gerekir."
  na "L7 (path/method) yetki için waypoint gerekir; gözlenen davranış bulgu olarak kaydedildi"
fi
check_true "zincir çalışıyor (gateway GET / -> order)" chain_ok probe-gateway
check_true "tüm shop pod'ları sağlıklı" shop_all_ready
expect_access "gateway: GET /"           izin probe-gateway "$SHOP_NS" "$O/"
expect_access "gateway: GET /api/orders" izin probe-gateway "$SHOP_NS" "$O/api/orders"
expect_access "gateway: GET /admin"      ret  probe-gateway "$SHOP_NS" "$O/admin"
expect_access "gateway: POST /"          ret  probe-gateway "$SHOP_NS" "$O/" -X POST
expect_access "gateway: DELETE /api/x"   ret  probe-gateway "$SHOP_NS" "$O/api/x" -X DELETE
expect_access "rogue: GET /"             ret  probe-rogue   "$SHOP_NS" "$O/"
metric deny_http_code "$(http_code probe-gateway "$SHOP_NS" "$O/admin")" kod "reddedilen endpoint'in cevabı"
