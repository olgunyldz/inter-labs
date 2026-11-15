# Test çerçevesi: katalog, koşu dizini, sonuç kaydı
#
# Her test: tests/<ID>/test.yaml (tanım) + tests/<ID>/run.sh (çalıştırıcı)
# Her koşu: results/<zaman>_<ID>_<mesh>_r<n>/
#   meta.json    test, mesh, profil, oturum, sürümler, git commit, başlangıç/bitiş, durum
#   result.json  durum + kontroller + metrikler + bulgular (rapor bunu okur)
#   raw/         ham çıktılar (k6 özetleri, Prometheus sorguları, kubectl çıktıları)
#   log.txt      koşunun tam logu
#
# run.sh içinde kullanılabilen yardımcılar:
#   check <ad> <beklenen> <gerçekleşen>     eşitlik kontrolü
#   check_true <ad> <komut...>              komut başarılıysa geçer
#   check_le / check_ge <ad> <değer> <sınır> sayısal sınır kontrolü
#   metric <anahtar> <değer> [birim] [açıklama]
#   finding <metin>                         rapora girecek bulgu
#   na <neden>                              bu mesh'te uygulanamaz (yetenek yok) -> durum "na"
#   on_exit <komut...>                      test bitince (hata olsa da) çalışacak temizlik

TESTS_DIR="$MEVAL_ROOT/tests"

# Çalışma sırası: performans -> güvenlik -> trafik -> gözlem -> dayanıklılık (R05 mesh'i yeniden kurar, en sonda)
test_ids() {
  local g
  for g in P S T O R; do
    find "$TESTS_DIR" -mindepth 2 -maxdepth 2 -name test.yaml -printf '%h\n' | xargs -n1 basename | grep "^$g" | sort
  done
}
test_meta() { python3 -c 'import sys,yaml,json; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))' "$TESTS_DIR/$1/test.yaml"; }

# test_supports <id> <mesh>: test.yaml'daki meshes listesi (yoksa hepsi)
test_supports() {
  test_meta "$1" | jq -e --arg m "$2" '(.meshes // ["all"]) | (index("all") != null or index($m) != null)' >/dev/null
}

_jsonl() { jq -cn "$@" >> "$RUN_DIR/$_JSONL_FILE"; }
check() {
  local pass=false; [ "$2" = "$3" ] && pass=true
  jq -cn --arg n "$1" --arg e "$2" --arg a "$3" --argjson p $pass '{name:$n, expected:$e, actual:$a, pass:$p}' >> "$RUN_DIR/checks.jsonl"
  if $pass; then ok "$1 (=$3)"; else fail "$1: beklenen=$2 gerçekleşen=$3"; fi
}
check_true() {
  local n=$1; shift
  if "$@" >/dev/null 2>&1; then check "$n" ok ok; else check "$n" ok hata; fi
}
check_le() {
  local pass=false; awk -v a="$2" -v b="$3" 'BEGIN{exit !(a+0 <= b+0)}' && pass=true
  jq -cn --arg n "$1" --arg e "<= $3" --arg a "$2" --argjson p $pass '{name:$n, expected:$e, actual:$a, pass:$p}' >> "$RUN_DIR/checks.jsonl"
  if $pass; then ok "$1 ($2 <= $3)"; else fail "$1: $2 > $3"; fi
}
check_ge() {
  local pass=false; awk -v a="$2" -v b="$3" 'BEGIN{exit !(a+0 >= b+0)}' && pass=true
  jq -cn --arg n "$1" --arg e ">= $3" --arg a "$2" --argjson p $pass '{name:$n, expected:$e, actual:$a, pass:$p}' >> "$RUN_DIR/checks.jsonl"
  if $pass; then ok "$1 ($2 >= $3)"; else fail "$1: $2 < $3"; fi
}
metric() {
  local v=$2
  [[ "$v" =~ ^-?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$ ]] || v=null
  jq -cn --arg k "$1" --argjson v "$v" --arg u "${3:-}" --arg d "${4:-}" '{key:$k, value:$v, unit:$u, desc:$d}' >> "$RUN_DIR/metrics.jsonl"
  printf '    %s = %s %s\n' "$1" "$2" "${3:-}" >&2
}
finding() { jq -cn --arg t "$*" '$t' >> "$RUN_DIR/findings.jsonl"; warn "BULGU: $*"; }
na() { echo "$*" > "$RUN_DIR/na.txt"; warn "uygulanamaz: $*"; exit 0; }
_ON_EXIT=()
on_exit() { _ON_EXIT+=("$*"); }
_run_on_exit() { local c; for c in "${_ON_EXIT[@]}"; do eval "$c" >/dev/null 2>&1 || true; done; }

# profile_val <quick-değer> <full-değer>
profile_val() { if [ "${PROFILE:-quick}" = full ]; then echo "$2"; else echo "$1"; fi; }

raw() { echo "$RUN_DIR/raw/$1"; }

# --- Koşu ---------------------------------------------------------------------
run_one() { # run_one <id> <tekrar-no>
  local id=$1 rep=$2 mesh ts dir status rc t0 t1
  mesh=$(current_mesh)
  ts=$(date +%Y%m%d-%H%M%S)
  dir="$RESULTS_DIR/${ts}_${id}_${mesh}_r${rep}"
  mkdir -p "$dir/raw"
  : > "$dir/checks.jsonl"; : > "$dir/metrics.jsonl"; : > "$dir/findings.jsonl"
  t0=$(date +%s)
  jq -n --argjson t "$(test_meta "$id")" --arg mesh "$mesh" --arg profile "$PROFILE" \
    --arg session "$SESSION" --argjson rep "$rep" --argjson start "$t0" \
    --argjson versions "$(versions_json)" --arg commit "$(git -C "$LAB_ROOT" rev-parse --short HEAD 2>/dev/null)" \
    --arg dirty "$(git -C "$LAB_ROOT" status --porcelain 2>/dev/null | wc -l)" \
    '{test:$t, mesh:$mesh, profile:$profile, session:$session, repeat:$rep, start:$start,
      versions:$versions, git:{commit:$commit, uncommitted_files:($dirty|tonumber)}}' > "$dir/meta.json"
  log "Test $id  [mesh=$mesh profil=$PROFILE tekrar=$rep]  -> ${dir#$MEVAL_ROOT/}"
  if ! test_supports "$id" "$mesh"; then
    echo "bu test $mesh profilinde tanımlı değil (test.yaml: meshes)" > "$dir/na.txt"
    rc=0
  else
    set +e
    (
      set -euo pipefail
      export RUN_DIR="$dir" MESH="$mesh" PROFILE TEST_ID="$id"
      trap _run_on_exit EXIT
      cd "$TESTS_DIR/$id"
      source ./run.sh
    ) 2>&1 | tee "$dir/log.txt"
    rc=${PIPESTATUS[0]}
    set -e
  fi
  t1=$(date +%s)
  if [ -f "$dir/na.txt" ]; then status=na
  elif [ "$rc" -ne 0 ]; then status=error
  elif jq -s -e 'any(.pass == false)' "$dir/checks.jsonl" >/dev/null 2>&1; then status=fail
  else status=pass; fi
  jq -n --arg s "$status" --argjson rc "$rc" --argjson start "$t0" --argjson end "$t1" \
    --arg na "$(cat "$dir/na.txt" 2>/dev/null)" \
    --slurpfile c "$dir/checks.jsonl" --slurpfile m "$dir/metrics.jsonl" --slurpfile f "$dir/findings.jsonl" \
    '{status:$s, exit_code:$rc, start:$start, end:$end, duration_s:($end-$start),
      na_reason:(if $na == "" then null else $na end), checks:$c, metrics:$m, findings:$f}' > "$dir/result.json"
  jq --arg s "$status" --argjson end "$t1" '.status=$s | .end=$end' "$dir/meta.json" > "$dir/meta.tmp" && mv "$dir/meta.tmp" "$dir/meta.json"
  case $status in
    pass) ok "$id: GEÇTİ ($((t1 - t0)) sn)" ;;
    na)   warn "$id: UYGULANAMAZ — $(cat "$dir/na.txt")" ;;
    fail) fail "$id: KONTROL BAŞARISIZ ($((t1 - t0)) sn)" ;;
    *)    fail "$id: HATA (çıkış kodu $rc) — log: ${dir#$MEVAL_ROOT/}/log.txt" ;;
  esac
  echo "$status" > "$dir/.status"
}

cmd_test() {
  local sub=${1:-list}; shift || true
  case $sub in
    list)
      python3 - "$TESTS_DIR" $(test_ids) <<'PY'
import sys, yaml
d = sys.argv[1]
print(f"{'ID':<5} {'KATEGORİ':<13} {'AD':<56} MESH")
for i in sys.argv[2:]:
    t = yaml.safe_load(open(f"{d}/{i}/test.yaml"))
    ms = t.get("meshes", ["all"])
    print(f"{i:<5} {t['category']:<13} {t['name'][:56]:<56} {'hepsi' if 'all' in ms else ','.join(ms)}")
PY
      ;;
    run)
      local ids=() repeat=1
      PROFILE=quick
      while [ $# -gt 0 ]; do
        case $1 in
          --profile) PROFILE=$2; shift 2 ;;
          --repeat) repeat=$2; shift 2 ;;
          all) mapfile -t ids < <(test_ids); shift ;;
          *) ids+=("$1"); shift ;;
        esac
      done
      [ ${#ids[@]} -gt 0 ] || die "test id gerekli (meval test list)"
      SESSION=${SESSION:-adhoc-$(date +%Y%m%d)}
      export PROFILE SESSION
      local id r
      for id in "${ids[@]}"; do
        [ -f "$TESTS_DIR/$id/test.yaml" ] || die "test bulunamadı: $id"
        for ((r = 1; r <= repeat; r++)); do run_one "$id" "$r"; done
      done ;;
    *) die "test: bilinmeyen alt komut $sub" ;;
  esac
}

cmd_results() {
  local n=30
  [ "${1:-}" = --last ] && n=$2
  printf '%-48s %-8s %s\n' KOŞU DURUM SÜRE
  for d in $(ls -1d "$RESULTS_DIR"/*/ 2>/dev/null | tail -n "$n"); do
    [ -f "$d/result.json" ] || continue
    printf '%-48s %-8s %ss\n' "$(basename "$d")" "$(jq -r .status "$d/result.json")" "$(jq -r .duration_s "$d/result.json")"
  done
}

# Tam değerlendirme: mesh'leri sırayla kurar, her birinde testleri koşar
cmd_suite() {
  local meshes=("${MESH_PROFILES[@]}") tests=() fresh=--fresh repeat=1 m
  PROFILE=quick
  while [ $# -gt 0 ]; do
    case $1 in
      --meshes) IFS=, read -r -a meshes <<<"$2"; shift 2 ;;
      --tests) IFS=, read -r -a tests <<<"$2"; shift 2 ;;
      --profile) PROFILE=$2; shift 2 ;;
      --repeat) repeat=$2; shift 2 ;;
      --no-fresh) fresh=""; shift ;;
      *) die "suite: bilinmeyen argüman $1" ;;
    esac
  done
  [ ${#tests[@]} -gt 0 ] || mapfile -t tests < <(test_ids)
  export SESSION=${SESSION:-suite-$(date +%Y%m%d-%H%M)}
  log "Oturum $SESSION: mesh'ler=${meshes[*]} testler=${#tests[@]} profil=$PROFILE tekrar=$repeat"
  for m in "${meshes[@]}"; do
    cmd_mesh use "$m" $fresh
    cmd_test run "${tests[@]}" --profile "$PROFILE" --repeat "$repeat"
  done
  log "Oturum tamam: $SESSION  ->  meval report --session $SESSION"
}

cmd_report() {
  local args=()
  while [ $# -gt 0 ]; do
    case $1 in
      --session) args+=(--session "$2"); shift 2 ;;
      --out) args+=(--out "$2"); shift 2 ;;
      *) die "report: bilinmeyen argüman $1" ;;
    esac
  done
  log "Rapor üretiliyor"
  local out
  out=$(python3 "$MEVAL_ROOT/report/generate.py" --results "$RESULTS_DIR" "${args[@]}")
  ok "HTML    : $out/rapor.html"
  ok "Markdown: $out/rapor.md"
  ok "Veri    : $out/veri.json"
}

cmd_docs() {
  python3 "$MEVAL_ROOT/report/docs.py" >/dev/null && ok "docs/mesh-eval/test-senaryolari.md güncellendi"
}
