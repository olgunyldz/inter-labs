# S01 — mTLS zorunluluğu ve şifreleme kanıtı
expect_access "mesh dışından düz HTTP -> order" ret probe-outside "$OUTSIDE_NS" "http://order.$SHOP_NS.svc:9090/"
probe_pod sniffer "$OUTSIDE_NS" default sniffer '{"spec":{"hostNetwork":true},"securityContext":{"privileged":true}}'
on_exit kb -n "$OUTSIDE_NS" delete deploy sniffer --wait=false
MARK="MEVAL$RANDOM$RANDOM"; CTRL="MEVALCTRL$RANDOM$RANDOM"
kb -n "$OUTSIDE_NS" exec deploy/sniffer -c probe -- bash -c \
  "timeout 10 tcpdump -i any -A -s 0 -n tcp 2>/dev/null > /tmp/cap.txt; echo \$(grep -c $MARK /tmp/cap.txt) \$(grep -c $CTRL /tmp/cap.txt)" > "$(raw sniff-count.txt)" &
SNIFF=$!
sleep 3
for i in $(seq 20); do http_code probe-gateway "$SHOP_NS" "http://order.$SHOP_NS.svc:9090/" -H "X-Meval-Marker: $MARK" >/dev/null; done
# Kontrol: mesh dışından gönderilen istek (reddedilse bile) ağa düz metin çıkar -> sniffer çalışıyor mu
for i in $(seq 3); do http_code probe-outside "$OUTSIDE_NS" "http://order.$SHOP_NS.svc:9090/" -H "X-Meval-Marker: $CTRL" >/dev/null; done
wait $SNIFF || true
read -r n c < "$(raw sniff-count.txt)"; n=${n:-0}; c=${c:-0}
metric marker_packets "$n" paket "mesh içi isteğin işaretinin ağda görüldüğü paket sayısı (0 = şifreli)"
metric control_packets "$c" paket "kontrol: mesh dışı düz isteğin işareti (>0 olmalı)"
check_ge "kontrol: yakalama çalışıyor (düz metin kontrol işareti görüldü)" "$c" 1
if [ "$n" -gt 0 ]; then
  check "ağ üzerinde trafik şifreli" evet hayır
  finding "Servisler arası trafik ağda düz metin: başlıklar ve gövde node üzerinde okunabiliyor ($n paket)."
else
  check "ağ üzerinde trafik şifreli" evet evet
fi
