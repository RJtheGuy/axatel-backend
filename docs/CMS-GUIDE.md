# How the Axatel CMS works

Written from the actual code (backend `c78f740`, frontend `e75a0a9`, 13 Sep 2026) and checked by running the backend and calling its API. Keep it in `docs/CMS-GUIDE.md` and update it when the code changes.

---

## 1. The big picture

The site is **headless**: the CMS stores content, the frontend draws it.

```
Visitor's browser
      │
      ▼
   nginx (port 80)
      │
      ├──► Nuxt frontend (axatel-frontend, Vue)  ── draws every page
      │         │  asks for content over HTTP
      │         ▼
      └──► Django + Wagtail (axatel, :8000)       ── stores content, serves /api/v2/ and /cms/
                │
                ▼
             MariaDB (content, users, contact requests)   +  /var/www/axatel/media (uploaded images/PDFs)
```

- **Editors** work in the Wagtail admin at **`/cms/`**. They never touch Vue code.
- **The frontend** (Nuxt, server-side rendered) calls the backend API on every page load, then renders the JSON with Vue components.
- **Django's own templates are not used** for the public site. The README's `templates/` and `static/css/main.css` sections describe an older version. Everything visible comes from `axatel-frontend/app/`.
- If the API is down, most pages still render: the frontend has built-in fallback content (see §6). That keeps the site up but can hide a broken CMS, so run `deploy/smoke-test.sh`.

### What happens when someone opens `/monitoraggio/traffico`

1. nginx passes the request to Nuxt.
2. Nuxt matches `app/pages/monitoraggio/[slug].vue`.
3. That page calls `GET /api/v2/pages/?type=monitoring.MonitoringPage&slug=traffico&fields=*`.
4. Wagtail returns the page's fields as JSON. **Only published pages are returned**; drafts come back as an empty list, and the page 404s.
5. Vue draws the header from `title`, `category`, `cover_image`, and the body by passing `body` (a list of blocks) to `BlockRenderer.vue`.
6. `BlockRenderer` looks up each block's `type` (e.g. `"cta"`) and renders the matching component (`CmsCta.vue`).

---

## 2. The page tree (must look like this in `/cms/` → Pages)

Wagtail pages live in a tree. **The URL is the path through the tree.** The frontend asks for specific page types and slugs, so the tree has to match.

```
Root
└── Home                                  (HomePage)              /
    ├── Monitoraggio                      (Indice Monitoraggio)   /monitoraggio/
    │   ├── Traffico, Cantieri, Gallerie,  (Argomento monitoraggio) /monitoraggio/<slug>/
    │   │   Frane, Fiumi, Aria, Alberi,
    │   │   Ponti, Edifici
    ├── Casi                              (Indice Casi di successo) /casi/
    │   └── <one per case study>          (Caso di successo)      /casi/<slug>/
    ├── News                              (Indice News)           /news/  (old /blog/ redirects here)
    │   └── <news posts>                  (Articolo News)         /news/<slug>/
    ├── Servizi                           (Indice Servizi)        /servizi/
    │   └── <services>                    (Servizio)              /servizi/<slug>/
    ├── Soluzioni                         (Indice Soluzioni)      /soluzioni/
    │   └── <12 solutions>                (Soluzione)             /soluzioni/<slug>/
    ├── Prodotti                          (Indice Prodotti)       /prodotti/
    │   └── <products>                    (Prodotto)              /prodotti/<slug>/
    ├── Azienda                           (Sezione informativa)   /azienda/
    │   └── Chi siamo, Bilancio…          (Pagina informativa)    /azienda/<slug>/
    ├── Approfondimenti                   (Sezione informativa)   /approfondimenti/
    │   ├── FAQ, Academy, News            (Pagina informativa)    /approfondimenti/<slug>/
    │   └── Glossario                     (Glossario)             /approfondimenti/glossario/
    └── <any other page>                  (Pagina generica)       /<slug>/
```

Required slugs: index pages `monitoraggio`, `casi`, `blog`, `servizi`, `soluzioni`, `prodotti`; monitoring topics `traffico cantieri gallerie frane fiumi aria alberi ponti edifici`. A page with the right title but the wrong **type** or **slug** will not show. The smoke test checks all of these.

---

## 3. Page types

All page types have the **Promote** tab (SEO title, meta description, social image) from `wagtailseo`, and support drafts, scheduled publishing, revisions and 301 redirects.

| Admin name | Model | Allowed under | Fields the editor fills in | Drawn by (frontend) |
|---|---|---|---|---|
| Home Page | `home.HomePage` | Root | Rotating hero phrases, hero quote, hero logo, **"Fiducia" panel (client logos, certifications)**, blocks | `pages/index.vue` — only the Fiducia strip is read (see §6) |
| Pagina generica | `home.FlexPage` | Home, another Pagina generica | Blocks only | `pages/[...slug].vue` (any URL no other page claims) |
| Indice Monitoraggio | `monitoring.MonitoringIndexPage` | Home | Intro (blocks) | `pages/monitoraggio/index.vue` |
| Argomento monitoraggio | `monitoring.MonitoringPage` | Indice Monitoraggio | Emoji icon, card text, category (Ambiente / Viabilità / Strutture), cover image, tags, blocks | `pages/monitoraggio/[slug].vue` |
| Indice Casi di successo | `casi.CasiIndexPage` | Home | Intro (plain text) | `pages/casi/index.vue` |
| Caso di successo | `casi.CasoSuccessoPage` | Indice Casi | Client, category, card description, cover image, tags, body (**rich text**, not blocks) | `pages/casi/[slug].vue` + homepage carousel |
| Indice News / Articolo News | `blog.BlogIndexPage` / `blog.BlogPost` (the code keeps the name "blog") | Home / Indice News | Author, date, cover, excerpt, blocks, tags | `pages/news/index.vue`, `pages/news/[slug].vue` |
| Indice Servizi / Servizio | `services.*` | Home / Indice Servizi | Emoji, card text, blocks, Schema.org type | `pages/servizi/index.vue`, `pages/[area]/[slug].vue` |
| Indice Soluzioni / Soluzione | `solutions.*` | Home / Indice Soluzioni | Group (Piattaforme/Sensori/Tecnologie/Servizi), eyebrow, card text, picture, blocks | `pages/soluzioni/index.vue`, `pages/soluzioni/[slug].vue` |
| Sezione informativa | `home.InfoIndexPage` | Home | Intro (plain text) | `pages/[...slug].vue` (lists its pages) |
| Pagina informativa | `home.InfoPage` | Sezione informativa | Eyebrow, introduction, picture, blocks | `pages/[area]/[slug].vue` → `components/content/InfoPageView.vue` |
| Glossario | `home.GlossaryPage` | Sezione informativa (one per section) | Eyebrow, introduction, **terms** (term, definition, other names) | same, as a searchable list |
| Indice Prodotti / Prodotto | `products.*` | Home / Indice Prodotti | Model code, category, tagline, picture, **specifications** (label + value rows), datasheet (uploaded PDF or link), blocks | `pages/prodotti/index.vue`, `pages/prodotti/[slug].vue` |

---

## 4. Blocks (the "+" picker inside a page body)

A **block** is one section of a page. Editors stack blocks to build a page. The list is defined once in `axatel/core/blocks.py` (`BODY_BLOCKS`), and each block has a matching Vue component registered in `axatel-frontend/app/components/cms/BlockRenderer.vue`.

| Block (admin label) | Type key | What it's for | Vue component |
|---|---|---|---|
| Hero | `hero` | Big title, subtitle, background image, button | `CmsHero.vue` |
| Testo | `rich_text` | Paragraphs, H2–H4, lists, links, PDF links | `CmsRichText.vue` |
| Immagine | `image` | Image with caption and alt text | `CmsImage.vue` |
| Citazione | `quote` | Pull quote | `CmsQuote.vue` |
| Invito all'azione | `cta` | Heading + text + button | `CmsCta.vue` |
| Card servizi | `service_cards` | Pick existing Servizio pages as cards | `CmsServiceCards.vue` |
| Due colonne | `columns` | Text/images side by side | `CmsColumns.vue` |
| Video | `video_embed` | YouTube/Vimeo URL | `CmsVideoEmbed.vue` |
| Download | `download` | A document from the library | `CmsDownload.vue` |
| Spaziatore | `spacer` | Vertical space | `CmsSpacer.vue` |
| Statistiche animate | `stats` | Numbers that count up (value + suffix + label) | `CmsStats.vue` |
| Diagramma di rete | `network_diagram` | Animated network diagram | `CmsNetworkDiagram.vue` |
| Card soluzioni | `solution_cards` | Free tiles with icon, text, link | `CmsSolutionCards.vue` |
| Griglia vantaggi | `feature_grid` | Icon + title + text grid | `CmsFeatureGrid.vue` |
| Testimonianza | `testimonial` | Quote with name, role, photo | `CmsTestimonial.vue` |
| Loghi partner | `partner_logos` | Row of logos | `CmsPartnerLogos.vue` |
| Griglia casi di successo | `portfolio_grid` | Case-study cards | `CmsPortfolioGrid.vue` |
| Sezione di testo | `text_section` | Heading + text + short "key point" pills | `CmsTextSection.vue` |
| Prodotto in evidenza | `product_feature` | Highlighted product box, links to its Prodotto page | `CmsProductFeature.vue` |
| Cosa misuriamo | `measures` | Quantities measured (name, unit, note) | `CmsMeasures.vue` |
| Come funziona (passaggi) | `steps` | Numbered steps | `CmsSteps.vue` |
| Schede dispositivi | `device_cards` | Pick Prodotto pages → cards with picture and link | `CmsDeviceCards.vue` |
| Casi di successo collegati | `case_cards` | Pick case studies → cards | `CmsCaseCards.vue` |
| Domande frequenti | `faq` | Questions that open one at a time; also sent to Google as FAQPage data | `CmsFaq.vue` |

The last two follow the chosen pages: rename or re-picture a product and every card showing it updates. Unpublished pages are left out automatically.

Text fields inside blocks support **bold, italic, link and "H" (highlight)**. Highlight wraps the text in `<span class="u-accent">`, which the frontend colours with the accent red.

---

## 5. Site-wide settings (`/cms/` → Impostazioni)

These are one-per-site forms, not pages. The frontend reads them from `GET /api/v2/site-settings/` and `GET /api/v2/themes/active/`.

| Setting | Controls | Notes |
|---|---|---|
| **Navigazione** | Top menu: items, dropdown columns, links; header button text/URL; English/French labels | Links should use "page" (follows slug changes); use "custom URL" only for anchors or external links. Every item, group and link has a **Visibile** switch: turn it off to hide it without deleting it. **If this is empty, the navbar uses `app/data/navigation.json`** instead. |
| **Footer** | Contact rows (phone, email, address), P.IVA, Codice Fiscale | Used by the homepage footer. |
| **Team** | The people on `/azienda/team`: name, photo, role and description (with optional English/French versions), **Visibile** switch, order (drag to reorder) | Read from `GET /api/v2/team/`. **While the list is empty the page shows the built-in example team** from `app/data/team.ts`. |
| **Chatbot** | On/off, window title, welcome text, suggested questions | The answers themselves are in **Snippets → Voci chatbot**. |
| **Tema** | Primary/background/accent/text colours, fonts, base size, type scale, corner radius, shadow, logo | Applied in the browser by `plugins/theme.client.ts` as CSS variables. Saving keeps one undo step. |

**Snippets → Voci chatbot:** each entry has several ways to ask a question (one per line) and one answer. Exactly one entry can be marked as the fallback answer. The bot matches visitor questions to these using a small AI model (`sentence-transformers`, loaded on first use; each Gunicorn worker loads its own copy, so it uses memory).

**Contact requests** (from `/contatti`) are stored in the database as `ContactSubmission`. There are three kinds: contact, application (with CV) and **quote request** ("Richiesta di preventivo": product/solution, type of structure, sites, timing, stored in *Dettagli preventivo*). The "Richiedi un preventivo" buttons on product and solution pages open the form in quote mode with the product already filled in. They are visible in the **Django admin at `/django-admin/`** → Richieste di contatto, **not** in `/cms/`. An email is sent to the addresses in `ADMIN_EMAILS` (see §8).

---

## 6. What is NOT editable in the CMS (hard-coded in the frontend)

This is the most important thing to know. Several pages look like CMS pages but their content lives in Vue/TypeScript files. Changing them needs a code change and a frontend rebuild.

| URL | Where the content really lives | Status |
|---|---|---|
| `/` homepage — hero phrases, quote, demo, "applicativi" | `app/pages/index.vue` (`dashboardConfig`) | **Hard-coded.** The CMS HomePage hero fields exist but the homepage never reads them. Only case studies and the footer come from the CMS. |
| `/soluzioni/<slug>` | CMS (Soluzione pages) | **Editable.** The built-in text in `app/data/contentPages.ts` is only a fallback, shown when a slug has no published Soluzione page. |
| "Come lavoriamo" steps and the closing "Hai un progetto?" box on solution/product pages | `i18n/messages-catalogue.ts` | Interface text, in IT/EN/FR. |
| `/monitoraggio/<slug>` | CMS (Argomento monitoraggio pages) | **Editable.** The built-in text in `app/data/monitoring.ts` is only a fallback, shown when a topic has no published page. |
| `/azienda/chi-siamo, bilancio-sostenibilita, invia-il-cv, diventa-partner` | CMS (Pagina informativa under Azienda) | **Editable** after `import_info_pages`. The text in `app/data/contentPages.ts` is only the fallback. |
| `/approfondimenti/glossario` | CMS (Glossario under Approfondimenti) | **Editable**: terms are rows in the page. `app/data/glossary.ts` is only the fallback. |
| `/approfondimenti/academy, news, faq` | built-in "coming soon" placeholders | Create a Pagina informativa with that slug under Approfondimenti to replace one (use the "Domande frequenti" block for the FAQ). `import_info_pages` creates the FAQ as a **draft** with 7 starter questions: review it and press Pubblica. |
| `/azienda/team` | CMS (Impostazioni → Team) | **Editable.** `app/data/team.ts` is only the example shown while the CMS list is empty. |
| Navbar (fallback) | `app/data/navigation.json` | Used only if Impostazioni → Navigazione is empty. |
| Homepage case studies (fallback) | `app/pages/index.vue` | Shown if the CMS has no published case studies. |
| `/articoli/*` | redirects 301 to `/casi/*` | Old URLs. |

**Recommendation:** move `companyPages` into the CMS, and make the homepage read the remaining HomePage fields. That's the main work left before editors can manage the whole site themselves.

---

## 7. How to… (editor tasks)

**Log in:** `http://<site>/cms/` with a Wagtail user. Create users in `/cms/` → Settings → Users. Give editors the "Editors" group, not superuser.

**Add or edit a monitoring topic**
1. Pages → Home → Monitoraggio → **Add child page** → *Argomento monitoraggio*.
2. Title, then **Slug** (Promote tab). It must be one of the slugs the menu links to, e.g. `traffico`.
3. Fill in icon, short description, category, cover image, then add blocks to the body.
4. **Publish.** "Save draft" alone does not show it on the site.

**Add a case study:** Pages → Home → Casi → Add child page → *Caso di successo*. Fill in client, category, description (card text) and cover image, write the body, publish. It appears on `/casi`, at `/casi/<slug>`, and in the homepage carousel (newest first).

**Add a new standalone page** (e.g. `/pubblica-amministrazione`): Pages → Home → Add child page → *Pagina generica* → build it with blocks → publish. It's live at `/<slug>/` immediately; no code change is needed. Add it to the menu in Impostazioni → Navigazione.

**Change the menu:** Impostazioni → Navigazione. Each "Voce di menu" is a top item. Add "Gruppi" to make a dropdown. Link to pages with the page chooser. Changes are item by item: add one entry with "+", drag to reorder, or switch **Visibile** off to hide one — the rest of the menu is untouched.

**Add a product:** Pages → Home → Prodotti → Add child page → *Prodotto*. Fill in category, tagline, picture, add specification rows, upload the datasheet PDF (or paste a link), publish. It appears in `/prodotti` under its category. To show it on a solution page, add a "Schede dispositivi" or "Prodotto in evidenza" block there and pick it.

**Show client logos / certifications on the homepage:** Pages → Home → edit → panel "Fiducia" → add logos (name, image, optional link) → publish. The strip above the footer appears only when at least one entry exists. Use only clients who agreed and certifications actually held.

**Import or top up content from the built-in defaults** (safe to repeat; never overwrites or deletes what editors made):
```
python manage.py seed_products --images /var/www/axatel-frontend/app/assets/immagini
python manage.py import_solution_pages --images /var/www/axatel-frontend/app/assets/immagini
python manage.py seed_monitoring --images /var/www/axatel-frontend/app/assets/immagini
python manage.py import_info_pages --images /var/www/axatel-frontend/app/assets/immagini
python manage.py seed_navigation            # add --dry-run to preview
python manage.py rename_blog_to_news        # once: Blog menu link → News (/news), old News placeholder hidden
```
Each command only adds what is missing (matched by slug, or by Italian label for the menu). Run `seed_products` before `import_solution_pages` so solution pages can link to products.

**Organisation chart on the team page:** each person has **Riporta a** (who they report to) and, for managers, **Guida il reparto** (the department they lead). When at least one person reports to someone, the page draws an org chart: lines only between a person and their manager, departments as separate branches. Save a new person once before choosing them in someone else's "Riporta a". Hiding a manager keeps their team attached to the next person up.

- **Riporta anche a** (optional, tick boxes): extra managers for people who answer to more than one person. The person stays placed under their main manager ("Riporta a"); each extra manager gets a thinner, lighter line, and the profile lists all of them under "Riporta a".
- **Etichetta sotto il nome** (top of Impostazioni → Team): what is printed under each name in the chart. *Reparto* (default) shows the department pill under the managers; *Ruolo* shows each person's role; *Ruolo e reparto* shows both; *Nessuna etichetta* shows only names. The profile always shows the role and department.

**Add or change a team member:** Impostazioni → Team → **+ Persona**. Fill in name and photo (square, at least 400×400 px), role and a short description; English/French versions are optional (empty = Italian text is shown). Drag people to change their order. Switch **Visibile** off to hide someone without deleting them. Save. The first person you add replaces the example team on the site.

**Change colours or fonts:** Impostazioni → Tema → save. Visitors see it on their next page load.

**Rename a page's URL:** change the slug and publish, then add a 301 in Settings → Redirects from the old path to the new one.

**SEO per page:** Promote tab → SEO title, search description, OG image. The sitemap at `/sitemap.xml` updates automatically.

**Preview:** the "Preview" button is configured to open `<FRONTEND_URL>/preview`, but the frontend has **no `/preview` page yet**, so it shows a 404. Until that exists, save a draft and check it after publishing.

---

## 8. Configuration (`/var/www/axatel/.env`)

| Variable | What it does |
|---|---|
| `DJANGO_SECRET_KEY` | Required. Keep it secret. |
| `DATABASE_URL` | e.g. `mysql://user:pass@localhost/axatel` |
| `REDIS_URL` | Cache; without it each worker uses its own memory cache |
| `ALLOWED_HOSTS` | Hostnames Django answers for, comma-separated. **Must include `127.0.0.1,localhost`**: the frontend calls the API at `127.0.0.1` when it builds pages, and without them every CMS page is missing from the HTML (product pages show "not found"). Add `new.axatel.it`, `axatel.it`, `www.axatel.it` when those go live. |
| `CSRF_TRUSTED_ORIGINS` | Full origins allowed to POST, e.g. `http://80.211.135.192,https://axatel.it` |
| `CORS_ALLOWED_ORIGINS` | Origins the browser may call the API from |
| `SITE_URL` | Public base URL; used to build absolute image/document links in API responses |
| `FRONTEND_URL` | Used for CMS preview links |
| `SECURE_SSL_REDIRECT` | Must stay `False` until HTTPS works, then `True` |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP for notifications (defaults to SendGrid) |
| `ADMIN_EMAILS` | **New.** Who is emailed about contact requests and server errors, comma-separated |
| `APP_DEBUG` | Never `True` in production |

Frontend (`axatel-frontend` service environment): `NUXT_API_INTERNAL_BASE` (server-side calls, e.g. `http://127.0.0.1:8000/api/v2`) and `NUXT_PUBLIC_API_BASE` (browser calls, the public URL of `/api/v2`).

---

## 9. For developers

**Adding a new kind of CMS page** (model → migration → API → Nuxt page → fallback → sitemap → import command → smoke test) is written up step by step, with Chi siamo as the worked example, in the "Adding a CMS Page to Axatel" guide. The short version: define the page type in a backend app's `models.py` (fields, `content_panels`, `api_fields`, `parent_page_types`), run `makemigrations`, add the Nuxt page that fetches it with `useCms()` and keeps a built-in fallback, add its type to `server/routes/sitemap.xml.ts`, and add a line to `deploy/smoke-test.sh`.


**API endpoints the frontend uses**

| Endpoint | Returns |
|---|---|
| `GET /api/v2/pages/?type=<app.Model>&fields=*` | Published pages of one type (add `&slug=`, `&order=`) |
| `GET /api/v2/pages/find/?html_path=/x/y/&fields=*` | One page by URL (custom: returns JSON instead of a redirect) |
| `GET /api/v2/site-settings/` | Navigation, footer, chatbot settings |
| `GET /api/v2/themes/active/` | Theme colours, fonts, logo |
| `POST /api/v2/contact/` | Contact form (honeypot field `website`, 1 per visitor per minute, 10 MB attachment max) |
| `POST /api/v2/chatbot/ask/` | `{"message": "..."}` → `{"response": "..."}` |
| `POST /api/v2/themes/restore/` | Undo last theme change (CMS users only) |

Try one on the server:
```bash
curl -s -H "Host: $(grep ^ALLOWED_HOSTS /var/www/axatel/.env | cut -d= -f2 | cut -d, -f1)" \
  "http://127.0.0.1:8000/api/v2/pages/?type=monitoring.MonitoringPage&fields=title,category" | python3 -m json.tool
```

**Add a new block type** (e.g. a sensor spec table)
1. Backend: define the block class in `core/blocks_sections.py` (or `blocks.py`) and add `("spec_table", SpecTableBlock())` to `BODY_BLOCKS` **once**.
2. `python manage.py makemigrations && python manage.py migrate` (StreamField block lists are recorded in migrations).
3. Frontend: create `app/components/cms/CmsSpecTable.vue` taking a `value` prop.
4. Add `spec_table: resolveComponent("CmsSpecTable")` to `componentMap` in `BlockRenderer.vue`.
5. Rebuild the frontend and restart both services.
If you skip step 4, the block is silently hidden on the live site (a warning shows only in dev).

**Add a field to a page type:** add it to the model and to `content_panels` (so editors see it) **and** to `api_fields` (so the API returns it), migrate, then use it in the Vue page.

**Local development:** `axatel/settings/dev.py` requires `DATABASE_URL` to point at MySQL/MariaDB. The frontend defaults to an API at `http://localhost:8001/api/v2`.

---

## 10. Known issues and fixes

Fixed in `axatel-backend-fixes.patch` (26 Sep 2026), each verified before and after:

| Problem | Effect | Fix |
|---|---|---|
| Contact-form rate limit keyed on `REMOTE_ADDR` | Behind nginx every visitor is `127.0.0.1`, so after one request **all visitors** got "wait a minute" for 60 s | Use `X-Real-IP` / `X-Forwarded-For` |
| `mail_admins()` with no `ADMINS` configured | **Nobody was ever emailed** about contact requests | `ADMINS` from new `ADMIN_EMAILS` env var |
| `POST /api/v2/themes/restore/` had no permission check | **Any visitor could roll back the site theme** | Only logged-in CMS users |
| `CSRF_TRUSTED_ORIGINS` defined twice in `base.py` | The `.env` value was silently ignored | One definition, read from `.env` |
| Chatbot returned Python exception text | Internal details shown to visitors | Generic message, error logged |

Still open:
- Homepage hero fields in the CMS are not used by the frontend (§6).
- Solution and company pages are hard-coded (§6).
- No `/preview` page for the CMS Preview button (§7).
- `deploy/nginx.conf` in the repo describes a Django-only setup and does **not** match the live server (where nginx fronts Nuxt). Copy the live config into the repo: `cp /etc/nginx/sites-enabled/<file> deploy/nginx.live.conf`.
- `torch` + `sentence-transformers` are large; four Gunicorn workers each load the model. Watch memory with `free -h`.
- `axatel-frontend/.tmp-hero-desktop.png` is a leftover screenshot committed to the repo.
