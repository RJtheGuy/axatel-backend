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
    │   ├── Traffico, Cantieri, Tunnel,    (Argomento monitoraggio) /monitoraggio/<slug>/
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

Required slugs: index pages `monitoraggio`, `casi`, `blog`, `servizi`, `soluzioni`, `prodotti`; monitoring topics `traffico cantieri tunnel frane fiumi aria alberi ponti edifici`. A page with the right title but the wrong **type** or **slug** will not show. A topic with no CMS page (e.g. Tunnel until someone creates it) is shown from the built-in list as "In arrivo"; to write it, add an *Argomento monitoraggio* under Monitoraggio with that slug (e.g. `tunnel`, category Viabilità), publish it and translate it. Topics that exist only in the CMS (e.g. Pareti rocciose) work the same way. The smoke test checks all of these.

---

## 3. Page types

All page types have the **Promote** tab (SEO title, meta description, social image) from `wagtailseo`, and support drafts, scheduled publishing, revisions and 301 redirects.

| Admin name | Model | Allowed under | Fields the editor fills in | Drawn by (frontend) |
|---|---|---|---|---|
| Home Page | `home.HomePage` | Root | **Prima schermata** (kicker, title in three parts, text, two buttons, "Monitoraggio attivo 24/7" on/off — empty = built-in text), rotating hero phrases, hero quote, hero logo, **"Fiducia" panel (client logos, certifications)**, blocks | `pages/index.vue`, `components/dashboard/Citazione.vue` |
| Pagina generica | `home.FlexPage` | Home, another Pagina generica | Blocks only | `pages/[...slug].vue` (any URL no other page claims) |
| Indice Monitoraggio | `monitoring.MonitoringIndexPage` | Home | Intro (blocks) | `pages/monitoraggio/index.vue` |
| Argomento monitoraggio | `monitoring.MonitoringPage` | Indice Monitoraggio | **📋 Meta** panel (see below; category = Ambiente / Viabilità / Strutture), **Riquadro bianco** on/off (off = picture sits on the page), emoji icon, blocks, tags. **Unpublish to hide a topic**: its page, card and sitemap entry disappear (the built-in text is used only while the CMS is unreachable); also switch its menu link's Visibile off | `pages/monitoraggio/[slug].vue` |
| Indice Casi di successo | `casi.CasiIndexPage` | Home | Intro (plain text) | `pages/casi/index.vue` |
| Caso di successo | `casi.CasoSuccessoPage` | Indice Casi | Client, category, *Data del progetto*, card description, cover image, tags, body (**rich text**, not blocks) | `pages/casi/[slug].vue` + homepage carousel |
| Indice News / Articolo News | `blog.BlogIndexPage` / `blog.BlogPost` (the code keeps the name "blog") | Home / Indice News | Index: introduction, *Quando non ci sono news* (title and text of the "Prossimamente" panel shown on /news while no article is published; empty = built-in text, translated). Article: author, date, cover, excerpt, blocks, tags | `pages/news/index.vue`, `pages/news/[slug].vue` |
| Indice Servizi / Servizio | `services.*` | Home / Indice Servizi | **📋 Meta** panel (see below), emoji, blocks, tags, Schema.org type | `pages/servizi/index.vue`, `pages/[area]/[slug].vue` |
| Indice Soluzioni / Soluzione | `solutions.*` | Home / Indice Soluzioni | Group (Piattaforme/Sensori/Tecnologie/Servizi), eyebrow, **📋 Meta** panel (see below), blocks, tags | `pages/soluzioni/index.vue`, `pages/soluzioni/[slug].vue` |
| Sezione informativa | `home.InfoIndexPage` | Home | Intro (plain text) | `pages/[...slug].vue` (lists its pages) |
| Pagina informativa | `home.InfoPage` | Sezione informativa | **📋 Meta** panel without the card fields (category, eyebrow, introduction, cover image, *Immagine nella pagina*), blocks, tags | `pages/[area]/[slug].vue` → `components/content/InfoPageView.vue` |
| Glossario | `home.GlossaryPage` | Sezione informativa (one per section) | Eyebrow, introduction, **terms** (term, definition, other names) | same, as a searchable list |
| Indice Prodotti / Prodotto | `products.*` | Home / Indice Prodotti | Model code, category, tagline, picture, **specifications** (label + value rows), datasheet (uploaded PDF or link), blocks | `pages/prodotti/index.vue`, `pages/prodotti/[slug].vue` |

### The "📋 Meta" panel (Monitoraggio, Soluzioni, Servizi, Pagine informative)

The same idea as *Meta caso* on the success stories, without client and date (`core/page_meta.py`, frontend `utils/pageMeta.ts`). Every field is optional; an empty field shows nothing.

| Field | What it does |
|---|---|
| Categoria | Red label above the text on the page and on the card. On Monitoraggio it is also the area filter (Ambiente / Viabilità / Strutture); on Soluzioni it replaces the menu group in the label; on informative pages it replaces the section name. |
| Immagine di copertina | Picture of the card (Monitoraggio, Soluzioni, Servizi) and of the page. Cards show it whole, never cropped. |
| Immagine nella pagina | *Accanto all'introduzione* (default, the look before this panel existed), *Grande, in apertura* (across the column, like a success story) or *Non mostrarla nella pagina* (card only). |
| Descrizione (card) | Card text; also the Google description when the Promote tab is empty. |
| Mostra titolo nella card | Switch off when the picture already contains the title (the title stays for screen readers and Google). A card without a picture always shows its title. Not on informative pages (no picture cards). |
| Tags | "#tag" list under the introduction, like on a success story (Monitoraggio cards show them too). |

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
| Prodotto in evidenza | `product_feature` | Highlighted product box: a red button to its Prodotto page, then any number of **Pulsanti** (each to a page, a PDF in Documenti or an address; outline or red) | `CmsProductFeature.vue` |
| Cosa misuriamo | `measures` | Quantities measured (name, unit, note) | `CmsMeasures.vue` |
| Come funziona (passaggi) | `steps` | Numbered steps | `CmsSteps.vue` |
| Schede dispositivi | `device_cards` | Pick Prodotto pages → cards with picture and link | `CmsDeviceCards.vue` |
| Casi di successo collegati | `case_cards` | Pick case studies → cards | `CmsCaseCards.vue` |
| Domande frequenti | `faq` | Questions that open one at a time; also sent to Google as FAQPage data | `CmsFaq.vue` |
| Modulo di contatto | `contact_form` | The contact form right on the page (no extra click): title, text, request type (contatto / collaborazione / candidatura / preventivo), switches for company, phone, message and attachment (CV). Requests arrive in Richieste di contatto. Remove the block to switch it off | `CmsContactForm.vue` |

The last two follow the chosen pages: rename or re-picture a product and every card showing it updates. Unpublished pages are left out automatically.

Text fields inside blocks support **bold, italic, link and "H" (highlight)**. Highlight wraps the text in `<span class="u-accent">`, which the frontend colours with the accent red.

---

## 5. Site-wide settings (`/cms/` → Impostazioni)

These are one-per-site forms, not pages. The frontend reads them from `GET /api/v2/site-settings/` and `GET /api/v2/themes/active/`.

| Setting | Controls | Notes |
|---|---|---|
| **Navigazione** | Top menu: items, dropdown columns, links; header button text/URL; English/French labels | Links should use "page" (follows slug changes); use "custom URL" only for anchors or external links. Every item, group and link has a **Visibile** switch: turn it off to hide it without deleting it. **If this is empty, the navbar uses `app/data/navigation.json`** instead. |
| **Footer** | Contact rows (phone, email, address), **Seguici (social)** — LinkedIn, Facebook… each with a Visibile switch — P.IVA, Codice Fiscale, **Pagine legali** (Privacy policy, Cookie policy), **Avviso sui cookie** (on/off, text in IT/EN/FR; empty = built-in text) | Used on every page. The cookie notice is information only (the site uses technical storage only, no consent needed): a bar at the bottom on the first visit with a link to the Cookie policy and an OK button; OK is remembered in the browser (`ax-cookie-notice-ok`). If analytics or advertising are ever added, it must become a real consent banner. An old "Seguici" contact row is replaced by the social list. The legal pages appear in the footer, and the privacy one is linked from the consent box of every form, only once they are **published**. |
| **Notifiche moduli** | Who receives the e-mail for each kind of request (contatto, preventivo, candidatura, collaborazione; several addresses separated by commas; empty = the contatto addresses), *Allega i documenti* (CV attached to the e-mail), *Conferma a chi scrive* and its text in IT/EN/FR (`{nome}` = the visitor's first name) | Sending needs the `EMAIL_*` lines in `.env` (§8). |
| **Logo e immagini del sito** | Logo (menu, footer, particle animation), optional separate particle logo, **Ala nelle intestazioni** (the wing next to page titles and in the home quote) | Empty = built-in files. SVG or transparent PNG. Read from `GET /api/v2/branding/`. |
| **Reindirizzamenti** (Wagtail) | Old address → new page or address | Served by the frontend (`server/middleware/cms-redirects.ts`, list from `GET /api/v2/redirects/`, refreshed every minute), in every language. Wagtail adds one by itself when a published page's slug changes. Old WordPress addresses: `manage.py import_old_redirects` (§7a). Old `/wp-content/…` file links are redirected too (to Documenti). |
| **Motori di ricerca** | *Consenti ai motori di ricerca di indicizzare il sito* | **The go-live switch for Google.** Off (default) = every page sends `X-Robots-Tag: noindex` and `robots.txt` blocks everything (`server/middleware/indexing.ts`, `server/routes/robots.txt.ts`, read from `GET /api/v2/indexing/` every minute). On a bare IP address or localhost it is never indexable, whatever the switch says. |
| **Team** | The people on `/azienda/team`: name, photo, role and description (with optional English/French versions), **Visibile** switch, order (drag to reorder) | Read from `GET /api/v2/team/`. **While the list is empty the page shows the built-in example team** from `app/data/team.ts`. |
| **Chatbot** | On/off, window title, welcome text, suggested questions | The answers themselves are in **Snippets → Voci chatbot**. |
| **Tema** | Primary/background/accent/text colours, fonts, base size, type scale, corner radius, shadow, logo | Applied in the browser by `plugins/theme.client.ts` as CSS variables. Saving keeps one undo step. |

**Chatbot (how it works and how to improve it):** it only ever sends answers that already exist; it never writes text of its own. Two sources, matched together by meaning (sentence embeddings, `paraphrase-multilingual-MiniLM-L12-v2`, so Italian, English and French questions all match): (1) the entries written in **Snippets → Voci chatbot**, which always win when they fit; (2) **the published site**, read automatically: every monitoring topic, product, solution, success story, glossary term and "Domande frequenti" block becomes an answer (its short description / card text, the FAQ answer, the term's definition) with a **Scopri di più →** link to the page, plus two list answers, "Cosa monitorate?" (published topics by area) and "Quali prodotti avete?". Publishing or unpublishing a page updates the chatbot within a minute; English/French answers come from the translated pages. So the best way to teach it about a product or topic is a good title and a clear short description on its page. Below `CHATBOT_THRESHOLD` similarity, or when two answers are too close (`CHATBOT_MARGIN`), it sends the fallback entry. The widget is `app/components/chat/AiChat.vue` (posts to `/api/v2/chatbot/ask/` with the visitor's language; the answer comes back with an optional page link). `CHATBOT_SITE_KNOWLEDGE=false` in `.env` switches the site answers off.
- Answers in English/French: fill **Risposta (EN)/(FR)** on each entry (`manage.py translate_settings` pre-fills them with the translation model; review them). Empty = Italian answer.
- **Snippets → Domande al chatbot**: what visitors asked (text only, kept 180 days), the entry or the page (*Risposta dal sito*) used and the similarity. Filter **Risposto: No** to see what is missing, then add those phrasings to an entry or create a new one.
- Thresholds from data: `manage.py evaluate_chatbot` (leave-one-out on the entries' own questions, also in English/French when the translation models are installed) prints accuracy and, per threshold, answered/correct, with a recommended `CHATBOT_THRESHOLD`; put it in `.env` and restart. Compare models with `--models a,b`.
- **Suggerimenti sulla pagina** (Impostazioni → Chatbot): after *Dopo quanti secondi* (default 20) on a page, a bubble above the chat button proposes questions about that page, e.g. on Monitoraggio frane "Come funziona il monitoraggio frane?" plus "Parla con un esperto". The questions come from the page itself (topic, product, solution, case study, list pages, the page's FAQs) and carry the answer's key, so clicking gives exactly that answer; other pages get a generic text and the *Domande suggerite*. Pages not translated yet get the generic suggestion in English/French. At most once per page per visit; "No grazie" stops them for the whole visit (sessionStorage `ax-chat-hint-seen`, `ax-chat-hint-off`, cleared when the tab closes: listed in the Cookie policy). Never while the chat is open, a form field is focused or the tab is hidden; hidden again after 25 s. *Pagine senza nuvoletta*: one address per line (default /contatti and the legal pages). Text and questions for one page: **Snippets → Suggerimenti del chatbot** (address, text and up to 3 questions per language). Questions chosen in the bubble show *Dalla nuvoletta* in Domande al chatbot. API: `GET /api/v2/chatbot/hint/?path=…&locale=…` (`chatbot/hints.py`, database only, no model); `POST /api/v2/chatbot/ask/` accepts `key` and `hint`.
- **Domande non chiare** (Impostazioni → Chatbot): before matching, `chatbot/understanding.py` checks that the message means something. Only filler or symbols ("uff", "boh", "ok", "?!?"), keyboard mashing ("asdfgh") or one or two words that appear nowhere in what the chatbot knows (example questions, answers and page titles in IT/EN/FR; plurals and one-letter typos tolerated) get the *Risposta a una domanda non chiara* text, which asks for a fuller question. A greeting alone ("ciao", "hello", "bonjour") gets the welcome message (Italian: *Messaggio di benvenuto*), thanks alone get "Prego!". A message that is exactly one of the example questions always goes to normal matching. In Domande al chatbot they show as *Domanda non chiara* (not answered), *Saluto* or *Ringraziamento*.
- **The widget follows Impostazioni → Chatbot** on the Italian site: *Titolo finestra*, *Messaggio di benvenuto*, *Testo segnaposto*, *Domande suggerite*; *Chatbot attivo* off removes the chat button from every page. English and French use the translated interface texts.
- Model on disk: `manage.py setup_chatbot_model` (models/chatbot/, not in git). Each Gunicorn worker loads its own copy (~0.5 GB with the multilingual model). Visitors are limited to 20 questions a minute.

**Snippets → Voci chatbot:** each entry has several ways to ask a question (one per line) and one answer. Exactly one entry can be marked as the fallback answer. The bot matches visitor questions to these using a small AI model (`sentence-transformers`, loaded on first use; each Gunicorn worker loads its own copy, so it uses memory).

**Contact requests** (from `/contatti`) are stored in the database as `ContactSubmission`. There are four kinds: contact, application (with CV), **partnership proposal** and **quote request** ("Richiesta di preventivo": product/solution, type of structure, sites, timing, stored in *Dettagli preventivo*). The "Richiedi un preventivo" buttons on product and solution pages open the form in quote mode with the product already filled in. They are visible in the **Django admin at `/django-admin/`** → Richieste di contatto, **not** in `/cms/`.

- **Privacy consent:** every form has a required box "Ho letto l'informativa privacy…" linking to the Privacy policy page; the API refuses a request without it (400). Each request stores the consent, the exact wording shown and the site language (`privacy_consent`, `consent_text`, `language`).
- **E-mails** (`core/notifications.py`): the request is always saved first. Then an e-mail goes to the recipients in Impostazioni → Notifiche moduli (fallback `ADMIN_EMAILS`), with every field, the CV/document attached when allowed, and *Reply-To* = the visitor, so "Rispondi" writes straight to them. If enabled, the visitor gets a short confirmation in the language they used. The outcome is stored on the request: column **E-mail** in Richieste di contatto (green = sent, red = failed, grey = received before this feature), the error text in *Errore di invio*. Select requests → action **Invia di nuovo la notifica e-mail**, or `manage.py resend_notifications [--days 30] [--dry-run]` after fixing the mail settings (failed sends only; `--include-older` adds the grey ones).
- **Test the mail settings:** `manage.py send_test_email [--to address]` sends one message and prints the exact SMTP error if it fails.
- **Legal pages:** `manage.py create_legal_pages [--dry-run]` creates `/privacy-policy` and `/cookie-policy` as **drafts** (Pagina generica) with a template written for this site (forms, CV, chatbot log, server logs; no tracking cookies; videos load only on click) and links them in Footer → Pagine legali. Complete the [DA COMPLETARE] parts, have the privacy adviser check the text, then publish; translate them like any page. Running it again changes nothing.
- **No cookie banner needed** while the site only uses technical storage (`ax-blog-seen`, `alarms` in the browser; `sessionid`, `csrftoken` for CMS users). YouTube/Vimeo blocks show a cover and load the player (youtube-nocookie.com, Vimeo with `dnt=1`) only when the visitor presses play. Adding analytics, maps, external chat or other third-party scripts would require a consent banner and an update of the Cookie policy.

---

## 6. What is NOT editable in the CMS (hard-coded in the frontend)

This is the most important thing to know. Several pages look like CMS pages but their content lives in Vue/TypeScript files. Changing them needs a code change and a frontend rebuild.

| URL | Where the content really lives | Status |
|---|---|---|
| `/` homepage — demo, "applicativi", explanation section | `app/pages/index.vue` (`dashboardConfig`) | **Hard-coded.** The first screen, hero phrases, quote, case studies, trust strip and footer come from the CMS. |
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

**Add a case study:** Pages → Home → Casi → Add child page → *Caso di successo*. Fill in client, category, description (card text) and cover image, write the body, publish. It appears on `/casi`, at `/casi/<slug>`, and in the homepage carousel. **Order:** by *Data del progetto* (when the project or event took place), most recent first; cases without a date come after the dated ones, most recently published first. Lists show every case (the API is read 20 at a time).

**Add a new standalone page** (e.g. `/pubblica-amministrazione`): Pages → Home → Add child page → *Pagina generica* → build it with blocks → publish. It's live at `/<slug>/` immediately; no code change is needed. Add it to the menu in Impostazioni → Navigazione.

**Change the menu:** Impostazioni → Navigazione. Each "Voce di menu" is a top item. Add "Gruppi" to make a dropdown. Link to pages with the page chooser. Changes are item by item: add one entry with "+", drag to reorder, or switch **Visibile** off to hide one — the rest of the menu is untouched.

**Arrange the columns of a dropdown:** each group has **Colonna**. *Automatica* (default) puts the group under the column that is shortest so far, so one long group and two short ones balance out. Choose *Colonna 1/2/3* to fix where a group goes (e.g. Strutture → Colonna 2 to sit under Viabilità); groups in the same column stack in the order of the list. Choosing *Colonna 3* makes that dropdown three columns wide. On phones the dropdown is always one list, in the order of the groups. To move a **link** from one group to another: add it in the new group (pick the same page) and delete it from the old one.

**Translating pages (self-hosted model, no outside service):** on any Italian page, **⋯ → Traduzione automatica (EN, FR)** queues it; within a minute the English/French version holds a **draft** with the translated title, Google title/description, texts, blocks (rich text keeps links and bold) and child items (e.g. glossary terms). Images, links, product choices, numbers and addresses are copied unchanged; the address (slug) stays the same as in Italian. Review and press **Pubblica** — nothing goes online by itself unless *Pubblica subito* is chosen (below). A translation whose English/French page has a draft waiting is skipped. An English/French page that was only a mirror of the Italian one (alias) becomes a real page, still showing the Italian text until its translation is published.
- **Snippets → Glossario di traduzione**: a term with no translation is a name kept exactly as written (product titles and the usual brand names are already included). A term with an English/French translation is always translated that way, e.g. *concessionarie stradali → road operators / concessionnaires routiers* (common monitoring terms such as crepa, galleria and casi di successo are built in). E-mail addresses, links, phone numbers and `{placeholders}` are always copied unchanged. After changing the glossary, run `translate_settings` again (fields made by the machine are redone, fields typed by hand are kept); for a page, request its translation again and review the new draft (corrections made in Memoria di traduzione are kept).
- **Snippets → Memoria di traduzione**: every translated text. Correct one and tick **Corretta a mano**: it is reused everywhere that text appears.
- **Snippets → Traduzioni richieste**: status and outcome of each request.
- **Impostazioni → Traduzione automatica**: *Traduci automaticamente* = every time an Italian page is published, its English and French versions are translated within a couple of minutes (cron). *Pubblica subito le traduzioni* = they go online without review (otherwise they wait as drafts). Corrections made in Memoria di traduzione are always reused. The "Traduzione automatica (EN, FR)" button also has a *Pubblica subito* box.
- Why visitors see "This page hasn't been translated yet": the English/French version of that page does not exist (or is only a mirror of the Italian one), so the Italian text is shown. Translate it (button, automatic setting or command) and publish it, and the notice disappears. Built-in "coming soon" pages (Academy, FAQ, News placeholders) are translated in the code and show no notice.
- Many pages at once: `python manage.py translate_pages --all --dry-run` (count) then without `--dry-run` (drafts) or with `--publish` (straight online); menu and team labels still empty in English/French: `python manage.py translate_settings`.
- How it works: Helsinki-NLP Opus-MT (`opus-mt-it-en`, `opus-mt-it-fr`, CC-BY 4.0) converted to CTranslate2 int8 by `manage.py setup_translation_models` into `TRANSLATION_MODEL_DIR` (default `models/mt`, not in git); run by `manage.py run_translation_jobs` every minute from cron (`deploy/translation.cron`), so the web workers never load it. Text handling (sentence splitting, rich text, protected names with placeholder retry) is in `translation/text.py`; quality is measured with `manage.py evaluate_translation` against the site's own human-translated interface texts (`translation/eval/interface.json`, chrF/BLEU via sacrebleu).

**Apply the requested corrections once:** `python manage.py apply_site_corrections [--dry-run]` puts the form on Diventa partner and Invia il CV (replacing the box that sent visitors to /contatti), adds LinkedIn and Facebook to the footer, and renames Gallerie to Tunnel (`/monitoraggio/tunnel`, menu label, redirect from the old address). Running it again changes nothing.

**Demo on the homepage:** each demo records its event when it ends (traffic flowing again, water back below the threshold…), and the Angel BPM window waits up to 90 s for it. Demo ids no longer need HTTPS (`utils/makeId.ts`): on plain `http://` the browser has no `crypto.randomUUID`, which used to drop every event.

**Buttons on a "Prodotto in evidenza" box:** under **Pulsanti** press "+" for each button: write the text, then choose a page of the site, *or* a PDF from Documenti (upload it there first, or straight from the chooser), *or* type an address. *Aspetto* picks outline or red. Drag to reorder. The old "Link alternativo" still works but holds one link only.

**PDFs live on this server:** `python manage.py localize_documents` copies the PDFs that pages still linked on www.axatel.it into Documenti and points product datasheets and "Prodotto in evidenza" boxes to them (pages are republished; a page with a draft waiting is listed and left alone). If the server cannot download them, put the files in a folder and add `--from-folder /that/folder`. The smoke test warns while any page still links a PDF on axatel.it.

**Add a product:** Pages → Home → Prodotti → Add child page → *Prodotto*. Fill in category, tagline, picture, add specification rows, upload the datasheet PDF in "Scheda tecnica (PDF)" (keep files on this server: avoid links to other sites), publish. It appears in `/prodotti` under its category. To show it on a solution page, add a "Schede dispositivi" or "Prodotto in evidenza" block there and pick it.

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

**Rename a page's URL:** change the slug and publish. Wagtail adds the redirect from the old address by itself (check it in Impostazioni → Reindirizzamenti).

**What is left to do (Report → Controllo contenuti):** one page in the CMS that lists, with a link to fix each one: test values and parts still in [square brackets], "Test:" titles, example names in the team, an invalid VAT number; links to the old www.axatel.it; menu entries pointing to unpublished pages; published pages with no content ("In arrivo"); cards without text or picture; drafts waiting; pages without their English/French version online; menu labels, team and chatbot answers without translation; missing form recipients or legal pages; pictures whose title is a file name; pages without a Google description. Read-only, recalculated each time it is opened. Same list on the server: `manage.py check_content [--summary] [--only placeholders,translations]` (code: `core/content_audit.py`). The smoke test shows the count.

**SEO per page:** Promote tab → SEO title, search description, OG image. The sitemap at `/sitemap.xml` updates automatically.

**Preview:** the "Preview" button is configured to open `<FRONTEND_URL>/preview`, but the frontend has **no `/preview` page yet**, so it shows a 404. Until that exists, save a draft and check it after publishing.

---

## 7a. Go-live, in order

1. **Form e-mails:** `EMAIL_*` in `.env` (§8), `manage.py send_test_email --to you@…`, recipients in Impostazioni → Notifiche moduli, send one request from `/contatti`.
2. **Privacy:** `manage.py create_legal_pages`, complete the [DA COMPLETARE] parts, adviser check, publish, translate.
3. **Content:** Report → Controllo contenuti until the first groups are empty (test values, old links, menu, empty pages) and the translations you need are published. Write the "In arrivo" topics or switch their menu entry off.
4. **Old addresses:** `manage.py import_old_redirects --propose` writes `/tmp/axatel-redirects.csv` with a proposed new address for each old one (built-in list from the old sitemaps, `core/data/old_site_urls.txt`; add more with `--urls file.txt`, e.g. the Google Search Console export, or `--sitemap URL`). Open it, check the *media* and *nessuna* rows, correct the *to* column, then `--apply /tmp/axatel-redirects.csv --dry-run` and without `--dry-run`. They appear in Impostazioni → Reindirizzamenti (editable, or import a CSV there too). Existing redirects are never overwritten without `--replace`.
5. **Domain and HTTPS** (last): DNS of axatel.it/www to this server, nginx `server_name`, certificate (`certbot --nginx -d axatel.it -d www.axatel.it`), then in `.env`: `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `SITE_URL` (also the base of CMS links in e-mails), `FRONTEND_URL`, `SECURE_SSL_REDIRECT=True`; frontend service: `NUXT_PUBLIC_I18N_BASE_URL=https://axatel.it` (sitemap, hreflang, robots) and `NUXT_PUBLIC_API_BASE`. Settings → Sites: hostname `axatel.it`. Restart both services, run the smoke test.
5a. **Pictures, documents and "Chi siamo" from the old site** (do it before the domain moves: afterwards www.axatel.it is this site and the old files are gone): `manage.py import_old_site_images` (on the server, which can reach www.axatel.it; no migration, nothing changes without an option). Without options it reports, for each Caso di successo and Prodotto, whether it has a picture and which old page/picture matches it (old site's WordPress API, else its pages' og:image), the text of the old /conosci-axatel/, and every document of the old site (PDF, Word, Excel, zip: its media library, else the files linked from its pages). Then: `--download` (zip at `/media/old-site/old-site-images.zip`, remove with `--clean-download`), `--import` (pictures into Immagini and documents into Documenti, collection *Sito precedente*, never twice: same file = same item), `--attach` (also sets the pictures as *Immagine di copertina* on pages that have none and no unpublished draft, and publishes that), `--chi-siamo-draft` (old text and pictures as a **draft** of Azienda → Chi siamo; preview and publish it in the CMS). With `--import`/`--attach` every copied file also gets a redirect from its old address (`/wp-content/uploads/…`) to the copy, so old links keep working after the switch (existing redirects are not changed). `--only casi|prodotti|chi-siamo|documenti`, `--min-score` (title similarity, default 0.35). Pictures and documents already uploaded are never replaced. Then run Report → Controllo contenuti: *Link al vecchio sito* lists any text or menu still pointing at www.axatel.it.
6. **Open to Google:** Impostazioni → Motori di ricerca → switch on. If an `add_header X-Robots-Tag` line was added by hand in `/etc/nginx/`, remove it (the smoke test says so). Submit `https://axatel.it/sitemap.xml` in Google Search Console and watch its "Pages" report for old addresses still giving 404: add them with `import_old_redirects --propose --urls export.csv`.

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
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_SSL` / `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP account the site sends from. Aruba: `smtps.aruba.it`, `465`, `EMAIL_USE_SSL=true`, the full mailbox address as user. Office 365: `smtp.office365.com`, `587`, `EMAIL_USE_TLS=true`. **Without `EMAIL_HOST` nothing is sent** (requests are still saved and flagged "not e-mailed"). Check with `manage.py send_test_email`. |
| `DEFAULT_FROM_EMAIL` | Sender shown, default `Sito Axatel <EMAIL_HOST_USER>`. Most providers require it to be the same mailbox as the user. |
| `ADMIN_EMAILS` | Who is emailed about server errors, comma-separated; also the recipients of form messages while Impostazioni → Notifiche moduli is empty |
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
