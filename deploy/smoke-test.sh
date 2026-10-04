#!/usr/bin/env bash
# smoke-test.sh — check that the whole Axatel site works end to end.
#
# Run on the server as root after every deploy (read-only, changes nothing):
#   bash /var/www/axatel/deploy/smoke-test.sh
#
# Exit code 0 = everything passed, 1 = something failed (so it can gate a deploy script).
set -uo pipefail

APP=/var/www/axatel
FRONT=/var/www/axatel-frontend
PY="$APP/venv/bin/python"
export DJANGO_SETTINGS_MODULE=axatel.settings.production

BACKEND="http://127.0.0.1:8000"
SITE="http://127.0.0.1"          # through nginx, like a real visitor

# Everything runs locally against this server only - it never contacts axatel.it.
# Host header: the server IP first, then any other host Django accepts.
HOST=""
for h in ${SMOKE_HOST:-} 80.211.135.192 127.0.0.1 \
         $(grep -E '^ALLOWED_HOSTS=' "$APP/.env" 2>/dev/null | cut -d= -f2- | tr -d '"'"'" | tr ',' ' '); do
  c=$(curl -s -o /dev/null -m 10 -w "%{http_code}" -H "Host: $h" "$BACKEND/api/v2/site-settings/")
  if [ "$c" != 400 ] && [ "$c" != 000 ]; then HOST=$h; break; fi
done
if [ -z "$HOST" ]; then
  echo "Django rejects every Host header (or is not running). Add 80.211.135.192 to ALLOWED_HOSTS in $APP/.env"
  HOST=80.211.135.192
fi

PASS=0; FAIL=0; WARN=0
ok()   { printf "  \e[32m✓\e[0m %s\n" "$1"; PASS=$((PASS+1)); }
bad()  { printf "  \e[31m✗\e[0m %s\n" "$1"; FAIL=$((FAIL+1)); }
warn() { printf "  \e[33m!\e[0m %s\n" "$1"; WARN=$((WARN+1)); }
section() { printf "\n\e[1m%s\e[0m\n" "$1"; }
code() { curl -s -o /dev/null -m 20 -w "%{http_code}" -H "Host: $HOST" "$@"; }

echo "Axatel smoke test — $(date '+%F %T') — Host: $HOST"

# ── 1. Services ──────────────────────────────────────────────────────────
section "1. Services"
for s in nginx axatel axatel-frontend mariadb redis-server; do
  [ "$(systemctl is-active $s)" = active ] && ok "$s running" || bad "$s NOT running  → systemctl status $s"
done
if ps -o user= -C gunicorn | grep -qv www-data; then
  bad "a Gunicorn process runs as root (started by hand)  → see SERVER-DEBUG.md 'Port 8000 taken'"
else
  ok "Gunicorn runs only as www-data"
fi
redis-cli ping 2>/dev/null | grep -q PONG && ok "redis answers" || bad "redis does not answer"

# ── 2. Django health ─────────────────────────────────────────────────────
section "2. Django"
cd "$APP"
if out=$(sudo -u www-data "$PY" manage.py check 2>&1); then ok "manage.py check"; else bad "manage.py check failed"; echo "$out" | tail -5; fi
pending=$(sudo -u www-data "$PY" manage.py showmigrations --plan 2>/dev/null | grep -c "^\[ \]")
[ "$pending" = 0 ] && ok "all migrations applied" || bad "$pending migration(s) not applied  → manage.py migrate"
deploy_warn=$(sudo -u www-data "$PY" manage.py check --deploy 2>&1 | grep -c "security.W")
[ "$deploy_warn" = 0 ] && ok "no security warnings" || warn "$deploy_warn security warning(s) (expected until HTTPS)  → manage.py check --deploy"
grep -qE '^ADMIN_EMAILS=.+' "$APP/.env" && ok "ADMIN_EMAILS set (contact notifications)" || warn "ADMIN_EMAILS missing in .env — nobody is emailed about contact requests"

# ── 3. API (Django directly) ─────────────────────────────────────────────
section "3. API"
for ep in site-settings/ themes/active/ "pages/?limit=1" images/?limit=1 team/ redirects/ branding/; do
  c=$(code "$BACKEND/api/v2/$ep"); [ "$c" = 200 ] && ok "/api/v2/$ep → 200" || bad "/api/v2/$ep → $c"
done
c=$(curl -s -o /dev/null -m 20 -w "%{http_code}" -H "Host: $HOST" -X POST "$BACKEND/api/v2/themes/restore/")
[ "$c" = 403 ] || [ "$c" = 401 ] && ok "theme restore blocked for visitors ($c)" || warn "theme restore returned $c to an anonymous visitor (fix not deployed?)"
# The frontend asks Django at 127.0.0.1 without a public Host header (see
# NUXT_API_INTERNAL_BASE). If ALLOWED_HOSTS lacks 127.0.0.1 every one of
# those requests is refused, and CMS pages are missing from the HTML.
c=$(curl -s -o /dev/null -m 20 -w "%{http_code}" "$BACKEND/api/v2/pages/?limit=1")
[ "$c" = 200 ] && ok "frontend can reach the API (127.0.0.1 allowed)" \
  || bad "API refuses the frontend's requests ($c)  → add 127.0.0.1,localhost to ALLOWED_HOSTS in $APP/.env"
c=$(code "$BACKEND/cms/login/"); [ "$c" = 200 ] && ok "CMS login page → 200" || bad "CMS login page → $c"
c=$(code "$BACKEND/sitemap.xml"); [ "$c" = 200 ] && ok "sitemap.xml → 200" || bad "sitemap.xml → $c"

# ── 4. CMS content the frontend expects ──────────────────────────────────
section "4. CMS pages (must exist AND be published)"
live_slugs() {
  curl -s -m 20 -H "Host: $HOST" "$BACKEND/api/v2/pages/?type=$1&fields=_,slug&limit=20" \
    | "$PY" -c 'import sys,json; print(" ".join(i["meta"]["slug"] for i in json.load(sys.stdin).get("items",[])))' 2>/dev/null
}
mon=$(live_slugs monitoring.MonitoringPage)
missing=""
for s in traffico cantieri frane fiumi aria ponti edifici; do
  [[ " $mon " == *" $s "* ]] || missing="$missing $s"
done
[ -z "$missing" ] && ok "monitoring topics are in the CMS" \
  || warn "not in the CMS yet:$missing (the site shows the built-in text)  → manage.py seed_monitoring"
info=$(live_slugs home.InfoPage)
missing=""
for s in chi-siamo bilancio-sostenibilita invia-il-cv diventa-partner; do
  [[ " $info " == *" $s "* ]] || missing="$missing $s"
done
[ -n "$(live_slugs home.GlossaryPage)" ] || missing="$missing glossario"
[ -z "$missing" ] && ok "Azienda pages and Glossario are in the CMS" \
  || warn "not in the CMS yet:$missing (the site shows the built-in text)  → manage.py import_info_pages"
# PDFs still served by the old WordPress site (www.axatel.it/wp-content/...)
old_pdfs=$(sudo -u www-data "$PY" manage.py localize_documents --dry-run 2>/dev/null | grep -oE "^[0-9]+ page\(s\) would" | grep -oE "^[0-9]+")
waiting=$(sudo -u www-data "$PY" manage.py localize_documents --dry-run 2>/dev/null | grep -c "draft waiting")
if [ "${old_pdfs:-0}" = 0 ] && [ "$waiting" = 0 ]; then ok "no page links PDFs on axatel.it"
else warn "${old_pdfs:-0} page(s) still link PDFs on axatel.it, $waiting with a draft waiting  → manage.py localize_documents"; fi
# One PDF that exists on disk must open through nginx; documents whose file
# is gone are listed separately (a CMS clean-up, not a server problem).
docs=$(sudo -u www-data "$PY" manage.py shell -c "
from wagtail.documents import get_document_model as g
ok=[d for d in g().objects.order_by('-id') if d.file and d.file.storage.exists(d.file.name)]
pdf=[d for d in ok if d.file.name.lower().endswith('.pdf')] or ok
print('URL', pdf[0].file.url if pdf else '')
print('MISSING', ', '.join(f'{d.title} (#{d.id})' for d in g().objects.order_by('id') if not (d.file and d.file.storage.exists(d.file.name))))
" 2>/dev/null)
doc=$(echo "$docs" | sed -n 's/^URL //p' | tail -1)
missing=$(echo "$docs" | sed -n 's/^MISSING //p' | tail -1)
if [ -n "$doc" ]; then
  c=$(code "$SITE$doc"); [ "$c" = 200 ] && ok "documents (PDF) open from this server ($doc)" || bad "document $doc → $c (nginx must serve /media/)"
fi
[ -z "$missing" ] && ok "every document in Documenti has its file" \
  || warn "file missing for: $missing  → CMS Documenti: upload the file again, or delete it if unused"
for t in casi.CasiIndexPage; do
  [ -n "$(live_slugs $t)" ] && ok "$t published" || bad "$t missing or not published"
done
n=$(live_slugs casi.CasoSuccessoPage | wc -w); [ "$n" -gt 0 ] && ok "$n case studies published" || warn "no case studies published (homepage shows built-in fallback)"

# ── 5. Frontend pages (through nginx, like a visitor) ────────────────────
section "5. Frontend pages"
ROUTES="/ /casi /monitoraggio /contatti /news /servizi /soluzioni /azienda/team /azienda/chi-siamo
/monitoraggio/traffico /monitoraggio/ponti /soluzioni/angel-bpm /soluzioni/lorawan /approfondimenti/glossario
/azienda/bilancio-sostenibilita /azienda/invia-il-cv /approfondimenti/faq /prodotti /prodotti/angel-river /prodotti/geo-angel /monitoraggio/aria /en /en/casi /robots.txt /sitemap.xml /feed.xml"
for r in $ROUTES; do
  c=$(code "$SITE$r")
  case "$c" in
    200) ok "$r → 200" ;;
    301|302|308) warn "$r → $c redirect" ;;
    *) bad "$r → $c" ;;
  esac
done
c=$(code "$SITE/questa-pagina-non-esiste-$$"); [ "$c" = 404 ] && ok "unknown page → 404" || warn "unknown page → $c (should be 404)"

c=$(code "$SITE/blog")
[ "$c" = 301 ] && ok "/blog → 301 to /news (old links keep working)" || warn "/blog → $c (expected a 301 redirect to /news)"
# Chatbot: model on disk (not downloaded while a visitor waits) and answering
if ls "$APP"/models/chatbot/*/modules.json >/dev/null 2>&1; then ok "chatbot model on disk (models/chatbot)"
else warn "chatbot model not on disk: downloaded at the first question  → manage.py setup_chatbot_model"; fi
c=$(curl -s -o /dev/null -m 90 -w "%{http_code}" -H "Host: $HOST" -H "X-Smoke-Test: 1" -H "Content-Type: application/json" \
    -X POST -d '{"message":"Dove siete?"}' "$BACKEND/api/v2/chatbot/ask/")
[ "$c" = 200 ] && ok "chatbot answers (/api/v2/chatbot/ask/)" || bad "chatbot → $c"
# Self-hosted translation: models converted and the job runner installed
if [ -f "$APP/models/mt/opus-mt-it-en/model.bin" ] && [ -f "$APP/models/mt/opus-mt-it-fr/model.bin" ]; then
  ok "translation models present (models/mt)"
else
  warn "translation models missing  → manage.py setup_translation_models"
fi
[ -f /etc/cron.d/axatel-translation ] && ok "translation job runner installed (cron)" \
  || warn "'Traduci' requests are not processed  → cp deploy/translation.cron /etc/cron.d/axatel-translation"
failed_jobs=$(sudo -u www-data "$PY" manage.py shell -c "from translation.models import TranslationJob as J; print(J.objects.filter(status='failed').count())" 2>/dev/null | tail -1)
[ "${failed_jobs:-0}" = 0 ] && ok "no failed translation requests" || warn "$failed_jobs failed translation request(s)  → CMS Snippets → Traduzioni richieste"
c=$(code "$SITE/monitoraggio/gallerie")
[ "$c" = 301 ] && ok "/monitoraggio/gallerie → 301 (renamed Tunnel; CMS redirects work)" || warn "/monitoraggio/gallerie → $c (expected a redirect to /monitoraggio/tunnel  → manage.py apply_site_corrections)"
forms=$(sudo -u www-data "$PY" manage.py apply_site_corrections --dry-run 2>/dev/null | grep -c "form already on the page")
[ "${forms:-0}" -ge 2 ] && ok "contact form on Diventa partner and Invia il CV" || warn "contact form not yet on Diventa partner / Invia il CV  → manage.py apply_site_corrections"

# ── 6. Not indexed by search engines (protects the live axatel.it) ────────
section "6. Search engines"
if curl -s -I -m 10 "$SITE/" | grep -qi "x-robots-tag:.*noindex"; then
  ok "noindex header present - Google won't index the IP site"
else
  warn "no X-Robots-Tag noindex header - the IP site could get indexed next to axatel.it"
fi

# ── 7. Errors logged in the last hour ────────────────────────────────────
section "7. Recent errors (last hour)"
# Only the running frontend (since its last restart), one line per failed
# request. "Page not found" visits are not logged, so they never count.
inv=$(systemctl show -p InvocationID --value axatel-frontend 2>/dev/null)
n=$(journalctl -u axatel-frontend ${inv:+_SYSTEMD_INVOCATION_ID=$inv} --since "1 hour ago" --no-pager 2>/dev/null | grep -E "\[request error\]|FAILED" | grep -vc "questa-pagina-non-esiste")
[ "$n" = 0 ] && ok "frontend log clean" || warn "$n error(s) in frontend log  → journalctl -u axatel-frontend --since '1 hour ago'"
# Only lines stamped within the last hour ("[2026-09-29 21:30:38 +0200] [ERROR] …").
since=$(date -d "1 hour ago" "+%Y-%m-%d %H:%M:%S")
n=$(awk -v s="$since" 'substr($0,2,19) >= s' /var/log/gunicorn/axatel_error.log 2>/dev/null | grep -ciE "\[ERROR\]|traceback")
[ "${n:-0}" = 0 ] && ok "backend log clean" || warn "$n error line(s) in backend log  → tail -n 80 /var/log/gunicorn/axatel_error.log"

# ── Summary ──────────────────────────────────────────────────────────────
printf "\n\e[1mResult: %d passed, %d warnings, %d failed\e[0m\n" "$PASS" "$WARN" "$FAIL"
[ "$FAIL" = 0 ]
