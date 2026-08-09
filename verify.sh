#!/usr/bin/env bash
#
# verify.sh — check that the CMS integration landed cleanly.
#
# Run from the repo root (/mnt/c/dev/axatel_cms):
#     bash verify.sh
#
# Read-only: makes no changes, only reports. Every check prints PASS,
# FAIL or WARN with an explanation of what to do about it.

set -uo pipefail

COMPOSE="docker compose -f docker-compose.dev.yml"
API="http://localhost:8001/api/v2"
FRONTEND_DIR="frontend/app"

pass=0; fail=0; warn=0

ok()   { echo "  PASS  $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL  $1"; [ -n "${2:-}" ] && echo "        → $2"; fail=$((fail+1)); }
note() { echo "  WARN  $1"; [ -n "${2:-}" ] && echo "        → $2"; warn=$((warn+1)); }
hdr()  { echo; echo "── $1 ────────────────────────────────────"; }

dj() { $COMPOSE exec -T web python manage.py "$@" 2>&1; }

# ═══════════════════════════════════════════════════════════════════
hdr "Containers"

if $COMPOSE ps --status running 2>/dev/null | grep -q web; then
    ok "web container running"
else
    bad "web container not running" "$COMPOSE up -d"
    echo; echo "Cannot continue without the web container."; exit 1
fi

if $COMPOSE ps --status running 2>/dev/null | grep -q frontend; then
    ok "frontend container running"
else
    note "frontend container not running" "$COMPOSE up -d frontend"
fi

if $COMPOSE ps -a 2>/dev/null | grep -q laravel; then
    note "laravel service still defined in docker-compose.dev.yml" \
         "It is unused now — remove the service block to stop the restart loop."
fi

# ═══════════════════════════════════════════════════════════════════
hdr "Django configuration"

CHECK=$(dj check)
if echo "$CHECK" | grep -q "no issues"; then
    ok "manage.py check clean"
else
    bad "manage.py check reported issues" "see output below"
    echo "$CHECK" | sed 's/^/        /'
fi

for app in casi home blog core services; do
    if dj shell -c "import ${app}; print('ok')" 2>/dev/null | grep -q ok; then
        ok "app importable: ${app}"
    else
        bad "app not importable: ${app}" "check INSTALLED_APPS and for syntax errors"
    fi
done

# ═══════════════════════════════════════════════════════════════════
hdr "Migrations"

PENDING=$(dj makemigrations --check --dry-run)
if echo "$PENDING" | grep -qi "no changes detected"; then
    ok "no unapplied model changes"
else
    bad "model changes not yet in a migration" "run: $COMPOSE exec web python manage.py makemigrations"
    echo "$PENDING" | sed 's/^/        /'
fi

UNAPPLIED=$(dj showmigrations --plan 2>/dev/null | grep -c "^\[ \]")
if [ "$UNAPPLIED" = "0" ]; then
    ok "all migrations applied"
else
    bad "$UNAPPLIED migration(s) unapplied" "run: $COMPOSE exec web python manage.py migrate"
fi

# ═══════════════════════════════════════════════════════════════════
hdr "Model fields and serializers"

dj shell -c "
from core.api_blocks import ImageAPIField, TagListField
print('serializers-ok')
" 2>/dev/null | grep -q serializers-ok \
  && ok "ImageAPIField / TagListField importable" \
  || bad "core/api_blocks.py missing the new serializers" "home, blog and casi all import these"

dj shell -c "
from home.models import HomePage
names = {f.name for f in HomePage._meta.get_fields()}
need = {'hero_frasi','hero_quote_text','hero_cases_logo'}
print('hero-ok' if need <= names else 'hero-missing:' + ','.join(sorted(need-names)))
" 2>/dev/null | grep -q hero-ok \
  && ok "HomePage has hero_frasi / hero_quote_text / hero_cases_logo" \
  || bad "HomePage missing new hero fields" "did home/models.py get replaced and migrated?"

dj shell -c "
from home.models import HomePage
print('casi-child-ok' if 'casi.CasiIndexPage' in HomePage.subpage_types else 'casi-child-missing')
" 2>/dev/null | grep -q casi-child-ok \
  && ok "HomePage.subpage_types includes casi.CasiIndexPage" \
  || bad "casi.CasiIndexPage not allowed under HomePage" "admin won't offer it as a child page"

for model_path in "blog.models:BlogPost" "casi.models:CasoSuccessoPage" "home.models:HomePage"; do
    mod="${model_path%%:*}"; cls="${model_path##*:}"
    n=$(dj shell -c "
from ${mod} import ${cls}
print(len(getattr(${cls}, 'api_fields', [])))
" 2>/dev/null | tr -d '\r' | tail -1)
    if [ "${n:-0}" -gt 0 ] 2>/dev/null; then
        ok "${cls}.api_fields declared (${n} fields)"
    else
        bad "${cls} has no api_fields" "its content will be invisible to the API"
    fi
done

# ═══════════════════════════════════════════════════════════════════
hdr "Content"

COUNTS=$(dj shell -c "
from casi.models import CasoSuccessoPage as C, CasiIndexPage as I
from home.models import HomePage
print(f'{HomePage.objects.count()},{I.objects.count()},{C.objects.count()},{C.objects.live().count()}')
" 2>/dev/null | tr -d '\r' | tail -1)

HOMES=$(echo "$COUNTS" | cut -d, -f1)
IDX=$(echo "$COUNTS" | cut -d, -f2)
CASI=$(echo "$COUNTS" | cut -d, -f3)
CASI_LIVE=$(echo "$COUNTS" | cut -d, -f4)

[ "${HOMES:-0}" -gt 0 ] 2>/dev/null \
  && ok "HomePage exists" \
  || bad "no HomePage" "create it in the Wagtail admin at /cms/"

[ "${IDX:-0}" -gt 0 ] 2>/dev/null \
  && ok "CasiIndexPage exists" \
  || bad "no CasiIndexPage" "run: $COMPOSE exec web python manage.py seed_casi"

if [ "${CASI:-0}" -ge 10 ] 2>/dev/null; then
    ok "$CASI caso pages seeded"
else
    bad "only ${CASI:-0} caso pages (expected 10)" "run: $COMPOSE exec web python manage.py seed_casi"
fi

if [ "${CASI_LIVE:-0}" -eq 0 ] 2>/dev/null && [ "${CASI:-0}" -gt 0 ] 2>/dev/null; then
    note "all $CASI caso pages are DRAFTS (live: 0)" \
         "The API only returns live pages, so the frontend will show fallback content. Publish them in the admin, or re-run seed_casi --publish."
elif [ "${CASI_LIVE:-0}" -gt 0 ] 2>/dev/null; then
    ok "$CASI_LIVE caso pages published"
fi

MISSING_IMG=$(dj shell -c "
from casi.models import CasoSuccessoPage as C
print(C.objects.filter(cover_image__isnull=True).count())
" 2>/dev/null | tr -d '\r' | tail -1)
if [ "${MISSING_IMG:-0}" -gt 0 ] 2>/dev/null; then
    note "$MISSING_IMG caso pages have no cover image" \
         "The seeder cannot import them. Upload in the admin; paths are in casi/casi_data.py."
else
    ok "all caso pages have a cover image"
fi

# ═══════════════════════════════════════════════════════════════════
hdr "API endpoints"

code() { curl -s -o /dev/null -w '%{http_code}' "$1" 2>/dev/null || echo 000; }
body() { curl -s "$1" 2>/dev/null; }

C=$(code "$API/pages/")
[ "$C" = "200" ] && ok "GET /api/v2/pages/ → 200" \
                 || bad "GET /api/v2/pages/ → $C" "is api_router mounted in urls.py?"

for t in home.HomePage casi.CasoSuccessoPage blog.BlogPost services.ServicePage; do
    C=$(code "$API/pages/?type=$t&fields=*&limit=1")
    [ "$C" = "200" ] && ok "type=$t → 200" || bad "type=$t → $C" "page type not registered?"
done

B=$(body "$API/pages/?type=casi.CasoSuccessoPage&fields=*&limit=1")
for f in '"body"' '"client"' '"category"' '"tags"' '"cover_image"'; do
    echo "$B" | grep -q "$f" && ok "casi API exposes $f" \
                             || note "casi API missing $f" "no live pages, or api_fields incomplete"
done

B=$(body "$API/pages/?type=blog.BlogPost&fields=*&limit=1")
if echo "$B" | grep -q '"items": \[\]'; then
    note "no live BlogPost pages to inspect" "cannot verify blog api_fields without content"
else
    for f in '"author"' '"body"' '"tags"'; do
        echo "$B" | grep -q "$f" && ok "blog API exposes $f" || bad "blog API missing $f" "blog/models.py api_fields"
    done
fi

C=$(code "$API/themes/active/")
[ "$C" = "200" ] && ok "GET /api/v2/themes/active/ → 200" \
                 || bad "GET /api/v2/themes/active/ → $C" \
                        "theme_views are not mounted — add them to urls.py BEFORE the api_router include"

C=$(code "http://localhost:8001/api/chatbot/chat/")
if [ "$C" = "405" ]; then
    ok "chatbot mounted (405 on GET is correct — it is POST-only)"
elif [ "$C" = "404" ]; then
    note "chatbot not at /api/chatbot/chat/" "check the prefix in the project urls.py"
else
    note "chatbot returned $C" "expected 405 for a GET"
fi

# ═══════════════════════════════════════════════════════════════════
hdr "Frontend files"

f_exists() {
    [ -f "$FRONTEND_DIR/$1" ] && ok "$1" || bad "$1 missing" "${2:-}"
}

f_exists "composables/useCms.ts"
f_exists "composables/carousel.ts"
f_exists "pages/index.vue"
f_exists "pages/casi/index.vue" "the listing page must be at pages/casi/index.vue, not pages/casi.vue"
f_exists "pages/casi/[slug].vue"
f_exists "pages/[...slug].vue"
f_exists "components/cms/BlockRenderer.vue"
f_exists "components/dashboard/CasiDiSuccesso.vue"

if [ -f "$FRONTEND_DIR/composables/carousel_with_stop.ts" ]; then
    bad "carousel_with_stop.ts still present" \
        "delete it — two files exporting useCarousel is what caused the duplicate-import warnings"
else
    ok "carousel_with_stop.ts removed"
fi

if [ -f "$FRONTEND_DIR/pages/casi.vue" ]; then
    bad "pages/casi.vue still present alongside pages/casi/" \
        "Nuxt will treat it as a parent layout and render blank. Move it to pages/casi/index.vue."
else
    ok "no conflicting pages/casi.vue"
fi

N=$(ls "$FRONTEND_DIR/components/cms/"Cms*.vue 2>/dev/null | wc -l)
[ "$N" -eq 17 ] && ok "17 Cms* block components present" \
                || bad "$N Cms* components (expected 17)" "some block types will not render"

if grep -rqs "successCases" "$FRONTEND_DIR/pages/" 2>/dev/null; then
    note "pages/ still references successCases" \
         "app/data/successCases.ts is superseded by the CMS — check for leftover imports"
fi

if [ -d "$FRONTEND_DIR/pages/articoli" ]; then
    note "pages/articoli/ still exists" \
         "nothing links there now; delete it or add a 301 to /casi/** in nuxt.config.ts"
fi

if grep -qs "prerender: true" ../nuxt.config.ts frontend/nuxt.config.ts 2>/dev/null; then
    note "prerender: true is set on a route" \
         "prerendered pages freeze CMS content at build time — edits will not appear until a rebuild"
fi

# ═══════════════════════════════════════════════════════════════════
hdr "Frontend build"

LOGS=$($COMPOSE logs --tail=300 frontend 2>/dev/null)

echo "$LOGS" | grep -q "Duplicated imports" \
  && bad "duplicate-import warnings still in the build" "carousel dedup did not take — restart the frontend container" \
  || ok "no duplicate-import warnings"

if echo "$LOGS" | grep -qiE "error|failed to resolve|cannot find module"; then
    bad "errors in the frontend log" "see below"
    echo "$LOGS" | grep -iE "error|failed to resolve|cannot find module" | tail -8 | sed 's/^/        /'
else
    ok "no errors in recent frontend log"
fi

# ═══════════════════════════════════════════════════════════════════
echo
echo "═══════════════════════════════════════════════════════════"
echo "  $pass passed · $fail failed · $warn warnings"
echo "═══════════════════════════════════════════════════════════"
[ "$fail" -gt 0 ] && echo "Fix the FAIL items first — WARNs are informational." && exit 1
echo "No failures. Check the browser pages listed in VERIFY.md next."
exit 0