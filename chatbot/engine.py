"""
The chatbot's matching engine. It never writes text: it finds the answer
whose example questions mean the same as the visitor's question.

Two kinds of answers are indexed together:
  - entries written by hand in Chatbot → Voci chatbot (they always win);
  - answers built from the published site (chatbot/site_knowledge.py):
    monitoring topics, products, solutions, success stories, glossary terms,
    FAQ blocks, and the lists "cosa monitorate?" / "quali prodotti avete?".

The index is rebuilt when an entry is saved or, checked at most once a
minute, when a page is published or unpublished. Questions already embedded
are kept, so a rebuild only encodes what is new.

Conversation (respond()): besides the matching above, the text of the pages
is indexed in short passages (passages.py), so an answer can quote the
paragraph that answers a detailed question, "Dimmi di più" continues with
the same page, a short follow-up ("e quanto costa?") is understood in the
light of the previous answer, and two equally close answers lead to a
question ("Intendi A o B?") instead of the fallback. The page's numbers
(vectors) are kept in the database (ChatbotVector) so a restart is fast;
`manage.py chatbot_warmup` computes them all at deploy time.
"""
import hashlib
import os
import re
import time
from pathlib import Path

import numpy as np
from django.conf import settings
from django.db.models import Max

from . import conversation as talk
from .models import ChatbotEntry, ChatbotVector
from .understanding import Vocabulary, classify, words

# The model is fetched once at deploy time (manage.py setup_chatbot_model)
# into models/chatbot/; it used to be downloaded on the first question into
# /tmp, which is wiped at reboot and fails when Hugging Face is unreachable.
os.environ.setdefault("HF_HOME", str(Path(settings.BASE_DIR) / "models" / "hf"))


def chatbot_model_path(name: str) -> Path:
    return Path(getattr(settings, "CHATBOT_MODEL_DIR", "") or Path(settings.BASE_DIR) / "models" / "chatbot") / name.replace("/", "__")


class _HashEncoder:
    """Stand-in for tests (CHATBOT_MODEL=hash): character 3-grams hashed into
    a vector. No download; good enough to check the logic, not for visitors."""

    def encode(self, texts, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False):
        out = np.zeros((len(texts), 2048), dtype=np.float32)
        for row, text in enumerate(texts):
            padded = f"  {text}  "
            for i in range(len(padded) - 2):
                out[row, hash(padded[i:i + 3]) % 2048] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norms == 0, 1, norms)


class ManualAnswer:
    """An entry of Voci chatbot, as the engine sees it."""

    def __init__(self, entry):
        self.key = f"entry:{entry.pk}"
        self.entry_id = entry.pk
        self.kind = "entry"
        self.label = str(entry)
        self.link = ""
        self.page_id = None
        self.titles = {}
        self.follow_ups = entry.follow_up_list
        self._entry = entry
        page = entry.page
        if page is not None and page.live:
            italian = page if page.locale.language_code == "it" else (
                page.get_translations(inclusive=True).filter(locale__language_code="it").first() or page)
            self.page_id = italian.pk
            self.link = re.sub(r"^https?://[^/]+", "", italian.url or "") or "/"
            self.titles = {"it": italian.title}

    def answer_in(self, language):
        return self._entry.answer_in(language)


class ChatbotEngine:
    THRESHOLD = float(os.environ.get("CHATBOT_THRESHOLD", "0.70"))
    MARGIN = float(os.environ.get("CHATBOT_MARGIN", "0.06"))
    # A site answer must beat a clear hand-written one by this much to be used.
    MANUAL_PRIORITY = float(os.environ.get("CHATBOT_MANUAL_PRIORITY", "0.05"))
    SITE_KNOWLEDGE = os.environ.get("CHATBOT_SITE_KNOWLEDGE", "true").lower() not in ("0", "false", "no")
    SITE_CHECK_SECONDS = 60
    # Multilingual: the answers are written in Italian and visitors ask in
    # Italian, English or French. (The old all-MiniLM-L6-v2 is English-only.)
    MODEL_NAME = os.environ.get("CHATBOT_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    # Page passages (respond()): how close a paragraph must be to be quoted.
    PASSAGE_MIN = float(os.environ.get("CHATBOT_PASSAGE_MIN", "0.50"))   # anywhere on the site
    CONTEXT_MIN = float(os.environ.get("CHATBOT_CONTEXT_MIN", "0.35"))   # in the page being discussed
    EXTRA_MIN = float(os.environ.get("CHATBOT_EXTRA_MIN", "0.45"))       # added under a page answer
    CLARIFY_MIN = float(os.environ.get("CHATBOT_CLARIFY_MIN", "0.60"))   # "Intendi A o B?"
    RELATED_MIN = float(os.environ.get("CHATBOT_RELATED_MIN", "0.45"))
    # Passages encoded during a visitor's request at most (the rest on the
    # next requests, or all at once with manage.py chatbot_warmup).
    ENCODE_BUDGET = int(os.environ.get("CHATBOT_ENCODE_BUDGET", "48"))
    PAGE_KINDS = ("topic", "product", "solution", "case", "service", "info")

    def __init__(self):
        self._model = None
        self._embeddings = None
        self._questions = []      # normalised text, one per indexed question
        self._owners = []         # answer key for each question
        self._manual_mask = None  # True where the question belongs to a hand-written entry
        self._answers = {}        # key → ManualAnswer / SiteAnswer
        self._fallback = ""
        self._fallback_id = None
        self._loaded_version = None
        self._site_version = None
        self._site_checked = 0.0
        self._vectors = {}        # normalised question → embedding (kept across rebuilds)
        self._vocabulary = None   # every word of the questions and answers (understanding.py)
        self._known = set()       # the example questions, as plain words
        self._all_passages = []   # every passage of the site (passages.py)
        self._passages = []       # the ones with a vector, in the same order as _p_matrix
        self._p_matrix = None
        self._passages_done = True
        self._page_answer = {}    # Italian page id → its answer key (topic:12, product:7…)
        self._page_vectors = {}   # answer key → average of its question vectors (related pages)

    @staticmethod
    def _normalize_text(value: str) -> str:
        if value is None:
            return ""
        text = value.lower()
        # Letters of any language (French ê, ï, œ... included), digits, spaces.
        text = re.sub(r"[^\w\s]+|_", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # -- loading -----------------------------------------------------------
    def _load_model(self):
        if self._model is not None:
            return
        if self.MODEL_NAME == "hash":
            self._model = _HashEncoder()
            return
        print("[Chatbot] Initializing model...")
        from sentence_transformers import SentenceTransformer

        local = chatbot_model_path(self.MODEL_NAME)
        source = str(local) if (local / "modules.json").exists() else self.MODEL_NAME
        self._model = SentenceTransformer(source, device="cpu")

    def _site_signature(self):
        if not self.SITE_KNOWLEDGE:
            return None
        now = time.monotonic()
        if self._site_version is not None and now - self._site_checked < self.SITE_CHECK_SECONDS:
            return self._site_version
        self._site_checked = now
        try:
            from .site_knowledge import signature
            self._site_version = signature()
        except Exception as error:  # noqa: BLE001 - the hand-written entries still work
            print(f"[Chatbot] Site knowledge unavailable: {error}")
            self._site_version = None
        return self._site_version

    def _ensure_loaded(self):
        latest = ChatbotEntry.objects.aggregate(latest=Max("updated_at"))["latest"]
        version = (latest, self._site_signature())
        if self._model is not None and version == self._loaded_version:
            if not self._passages_done:
                self._index_passages(self.ENCODE_BUDGET)
            return
        self._load_model()
        self._rebuild()
        self._loaded_version = version

    # -- vectors, kept in memory and in the database ---------------------------
    def _vector_key(self, text: str) -> str:
        return hashlib.sha1(f"{self.MODEL_NAME}|{text}".encode()).hexdigest()

    def _vectors_for(self, texts, budget=None):
        """text → vector for the texts given: from memory, then the database,
        then the model (at most `budget` texts computed now; None = all)."""
        wanted = [t for t in dict.fromkeys(texts) if t and t not in self._vectors]
        if wanted and self.MODEL_NAME != "hash":
            keys = {self._vector_key(t): t for t in wanted}
            try:
                found = list(keys)
                for start in range(0, len(found), 500):
                    for row in ChatbotVector.objects.filter(key__in=found[start:start + 500]):
                        self._vectors[keys[row.key]] = np.frombuffer(bytes(row.vector), dtype=np.float32)
            except Exception as error:  # noqa: BLE001 - the model can still compute them
                print(f"[Chatbot] Vector cache unavailable: {error}")
            wanted = [t for t in wanted if t not in self._vectors]
        if wanted:
            batch = wanted if budget is None else wanted[:budget]
            if batch:
                vectors = self._model.encode(batch, convert_to_numpy=True, normalize_embeddings=True,
                                             show_progress_bar=False).astype(np.float32)
                self._vectors.update(zip(batch, vectors))
                if self.MODEL_NAME != "hash":
                    try:
                        ChatbotVector.objects.bulk_create(
                            [ChatbotVector(key=self._vector_key(t), vector=v.tobytes()) for t, v in zip(batch, vectors)],
                            ignore_conflicts=True, batch_size=200)
                    except Exception as error:  # noqa: BLE001
                        print(f"[Chatbot] Could not store vectors: {error}")
        return {t: self._vectors[t] for t in texts if t in self._vectors}

    def _index_passages(self, budget=None):
        texts = [p.search_text for p in self._all_passages]
        vectors = self._vectors_for(texts, budget)
        self._passages = [p for p in self._all_passages if p.search_text in vectors]
        self._p_matrix = np.array([vectors[p.search_text] for p in self._passages]) if self._passages else None
        self._passages_done = len(self._passages) == len(self._all_passages)
        if self._passages_done and self._all_passages:
            print(f"[Chatbot] {len(self._passages)} page passages indexed.")

    def warm_up(self):
        """Every vector computed and stored (manage.py chatbot_warmup)."""
        self._ensure_loaded()
        self._index_passages(None)
        return len(self._questions), len(self._passages)

    def _rebuild(self):
        existing_fallback = self._fallback
        questions, owners, manual, answers = [], [], [], {}
        self._fallback, self._fallback_id = "", None

        def add(answer, texts, is_manual):
            seen = set()
            for text in texts:
                normalized = self._normalize_text(text)
                if not normalized or normalized in seen:
                    continue
                seen.add(normalized)
                questions.append(normalized)
                owners.append(answer.key)
                manual.append(is_manual)
            answers[answer.key] = answer

        for entry in ChatbotEntry.objects.select_related("page").all():
            if not entry.active:
                continue
            if entry.is_fallback:
                self._fallback = entry.answer.strip()
                self._fallback_id = entry.pk
                continue
            add(ManualAnswer(entry), entry.questions_list, True)

        site_count = 0
        if self.SITE_KNOWLEDGE:
            try:
                from .site_knowledge import build
                for answer in build():
                    add(answer, answer.questions, False)
                    site_count += 1
            except Exception as error:  # noqa: BLE001
                print(f"[Chatbot] Site knowledge skipped: {error}")

        self._questions, self._owners, self._answers = questions, owners, answers
        # What the chatbot can talk about, in all three languages: used to
        # recognise "uff", "boh" or "asdfgh" before any matching.
        texts = list(questions)
        for answer in answers.values():
            texts.append(answer.label)
            for language in ("it", "en", "fr"):
                texts.append(answer.answer_in(language))
            texts += list(getattr(answer, "titles", {}).values()) + list(getattr(answer, "labels", {}).values())
        self._vocabulary = Vocabulary(texts)
        self._known = {" ".join(words(q)) for q in questions}
        self._manual_mask = np.array(manual, dtype=bool)
        if not questions:
            self._embeddings = None
            self._fallback = self._fallback or existing_fallback
            print("[Chatbot] No ChatbotEntry rows found - run `manage.py seed_chatbot_kb`.")
            return

        vectors = self._vectors_for(questions)
        self._embeddings = np.array([vectors[q] for q in questions])

        # A hand-written entry about a page ("cos'è Angel River?") without a
        # "Pagina collegata" gets that page: its link, "Dimmi di più" and
        # follow-ups then work as for the page's own answer.
        titled = sorted(((self._normalize_text(a.titles.get("it", "")), a) for a in answers.values()
                         if a.kind in self.PAGE_KINDS and getattr(a, "titles", None)),
                        key=lambda t: len(t[0]), reverse=True)
        for answer in answers.values():
            if answer.kind != "entry" or answer.page_id:
                continue
            asked = [f" {self._normalize_text(q)} " for q in answer._entry.questions_list]
            for title, page in titled:
                if len(title) >= 4 and any(f" {title} " in q for q in asked):
                    answer.page_id, answer.link, answer.titles = page.page_id, page.link, dict(page.titles)
                    break

        # Pages: their answer, the average of their questions (to find related
        # pages) and their text in passages.
        self._page_answer, self._page_vectors = {}, {}
        owners = np.array(owners)
        for answer in answers.values():
            if getattr(answer, "page_id", None) and answer.kind in self.PAGE_KINDS:
                self._page_answer.setdefault(answer.page_id, answer.key)
                rows = self._embeddings[owners == answer.key]
                if len(rows):
                    mean = rows.mean(axis=0)
                    self._page_vectors[answer.key] = mean / (np.linalg.norm(mean) or 1)
        try:
            from .passages import build as build_passages
            self._all_passages = build_passages() if self.SITE_KNOWLEDGE else []
        except Exception as error:  # noqa: BLE001 - answers without passages still work
            print(f"[Chatbot] Page passages skipped: {error}")
            self._all_passages = []
        self._index_passages(self.ENCODE_BUDGET)
        print(f"[Chatbot] Ready. Indexed {len(questions)} questions "
              f"({int(self._manual_mask.sum())} written by hand, {site_count} answers from the site).")

    # -- answering -----------------------------------------------------------
    def answer(self, query: str) -> str:
        """Best matching answer text (Italian), or the fallback."""
        text, meta = self.answer_with_scores(query)
        if meta.get("special"):
            from .understanding import REPLIES
            return REPLIES[meta["special"]]["it"]
        return text

    def get_answer(self, key):
        """The ManualAnswer / SiteAnswer behind meta['answer_key']."""
        return self._answers.get(key)

    def _best(self, scores, mask):
        """(best index, its score, margin to the best other answer) within mask."""
        candidates = np.where(mask)[0]
        if not len(candidates):
            return None, 0.0, 0.0
        order = candidates[np.argsort(scores[candidates])[::-1]]
        best = int(order[0])
        second = next((int(i) for i in order[1:] if self._owners[i] != self._owners[best]), None)
        best_score = float(scores[best])
        return best, best_score, best_score - (float(scores[second]) if second is not None else 0.0)

    def answer_with_scores(self, query: str, vector=None) -> tuple:
        """Same as answer(), plus the numbers behind the decision.

        Used by chatbot_test / evaluate_chatbot so THRESHOLD and MARGIN can
        be set from real measurements rather than guesses.
        """
        self._ensure_loaded()

        def fallback(reason, best=0.0, margin=0.0, matched=None):
            return self._fallback or "Il chatbot non e ancora configurato.", {
                "best_score": round(best, 4), "second_score": round(best - margin, 4), "margin": round(margin, 4),
                "matched_question": matched, "used_fallback": True, "reason": reason,
                "entry_id": self._fallback_id, "answer_key": None, "source": "", "link": "",
            }

        if not (query or "").strip():
            return fallback("empty query")
        if self._embeddings is None:
            return fallback("knowledge base empty")

        # "uff", "ok", "asdfgh", "?!?", "ciao", "grazie": no matching (understanding.py).
        kind = classify(query, self._vocabulary, self._known)
        if kind:
            return "", {
                "best_score": 0.0, "second_score": 0.0, "margin": 0.0, "matched_question": None,
                "used_fallback": kind == "unclear", "reason": kind, "special": kind,
                "entry_id": None, "answer_key": None, "source": "", "link": "",
            }

        if vector is None:
            vector = self._encode(query)
        scores = self._embeddings @ vector

        m_idx, m_score, m_margin = self._best(scores, self._manual_mask)
        s_idx, s_score, s_margin = self._best(scores, ~self._manual_mask)
        manual_clear = m_idx is not None and m_score >= self.THRESHOLD and m_margin >= self.MARGIN
        site_clear = s_idx is not None and s_score >= self.THRESHOLD and s_margin >= self.MARGIN

        # Hand-written entries win unless a site answer is clearly closer.
        if manual_clear and not (site_clear and s_score > m_score + self.MANUAL_PRIORITY):
            chosen, score, margin = m_idx, m_score, m_margin
        elif site_clear:
            chosen, score, margin = s_idx, s_score, s_margin
        else:
            top, top_score, top_margin = max(
                [(m_idx, m_score, m_margin), (s_idx, s_score, s_margin)], key=lambda t: t[1])
            matched = self._questions[top] if top is not None else None
            reason = "below THRESHOLD" if top_score < self.THRESHOLD else "margin too small"
            return fallback(reason, top_score, top_margin, matched)

        answer = self._answers[self._owners[chosen]]
        return answer.answer_in("it"), {
            "best_score": round(score, 4), "second_score": round(score - margin, 4), "margin": round(margin, 4),
            "matched_question": self._questions[chosen], "used_fallback": False, "reason": "",
            "entry_id": getattr(answer, "entry_id", None), "answer_key": answer.key,
            "source": "" if answer.kind == "entry" else answer.label, "link": answer.link,
        }

    # -- conversation ----------------------------------------------------------
    def _encode(self, text: str):
        return self._model.encode([self._normalize_text(text)], convert_to_numpy=True,
                                  normalize_embeddings=True, show_progress_bar=False)[0]

    def _title(self, answer, language: str) -> str:
        titles = getattr(answer, "titles", None) or {}
        title = titles.get(language) or titles.get("it")
        if title:
            return title
        label = getattr(answer, "label", "") or ""
        return label.split(": ", 1)[-1].replace("[FALLBACK] ", "")

    def _page_passages(self, page_id, language: str):
        """The page's passages in reading order, in the visitor's language
        when the page is translated, otherwise in Italian."""
        own = [p for p in self._passages if p.page_id == page_id]
        chosen = [p for p in own if p.language == language] or [p for p in own if p.language == "it"]
        return sorted(chosen, key=lambda p: p.order)

    def _rank_passages(self, vectors, query: str, language: str, page_id=None, exclude=()):
        """[(score, words in common, passage)], best first. The score is the
        closeness to the question (best of the given vectors) plus a small
        bonus for each subject word the passage shares with the question."""
        if self._p_matrix is None:
            return []
        rows = [i for i, p in enumerate(self._passages)
                if (page_id is None or p.page_id == page_id) and p.id not in exclude]
        if not rows:
            return []
        in_language = [i for i in rows if self._passages[i].language == language]
        rows = in_language or [i for i in rows if self._passages[i].language == "it"]
        if not rows:
            return []
        matrix = self._p_matrix[rows]
        scores = np.max(np.stack([matrix @ v for v in vectors]), axis=0)
        ranked = []
        for i, score in zip(rows, scores):
            passage = self._passages[i]
            common = talk.overlap(query, passage.search_text)
            ranked.append((float(score) + 0.03 * min(common, 3), common, passage))
        ranked.sort(key=lambda r: r[0], reverse=True)
        return ranked

    def _answer_ranking(self, vector):
        """[(answer key, best score)] over all answers, best first."""
        scores = self._embeddings @ vector
        best = {}
        for index in np.argsort(scores)[::-1][:60]:
            key = self._owners[index]
            if key not in best:
                best[key] = float(scores[index])
        return sorted(best.items(), key=lambda kv: kv[1], reverse=True)

    def _related(self, key, language: str, limit=2):
        vector = self._page_vectors.get(key)
        if vector is None:
            return []
        scored = [(float(v @ vector), k) for k, v in self._page_vectors.items() if k != key]
        scored.sort(reverse=True)
        chips = []
        for score, other in scored:
            if score < self.RELATED_MIN or len(chips) >= limit:
                break
            answer = self._answers.get(other)
            if answer is not None and (language == "it" or (getattr(answer, "titles", {}) or {}).get(language)):
                chips.append({"type": "ask", "label": self._title(answer, language), "key": other})
        return chips

    def respond(self, query: str, language: str = "it", context=None, options=None, key=None) -> dict:
        """One turn of a conversation.

        context: what the chat sent back from the previous answer,
                 {"key": answer key, "shown": [passage ids already shown]}.
        options: {"page_text", "related", "contact"} (Impostazioni → Chatbot).
        key:     the answer of a question picked in a page suggestion or a
                 button (no matching: exactly that answer).

        Returns {"text", "link", "link_label", "kind", "answer_key", "chips",
        "context", "meta"}; kind is entry, page, passage, context, more,
        clarify, fallback, greeting, thanks or unclear.
        """
        self._ensure_loaded()
        language = language if language in ("it", "en", "fr") else "it"
        options = {"page_text": True, "related": True, "contact": True, **(options or {})}
        context = context if isinstance(context, dict) else {}
        current = self._answers.get(str(context.get("key") or ""))
        shown = {str(i) for i in (context.get("shown") or [])[:60]}
        current_page = getattr(current, "page_id", None)

        def contact_chip():
            return [{"type": "contact", "label": talk.text("contact", language)}] if options["contact"] else []

        def result(kind, text, answer=None, link="", chips=None, new_shown=(), meta=None, keep_context=False):
            key = answer.key if answer is not None else (current.key if (keep_context and current) else None)
            seen = (shown if (keep_context or (answer is not None and current is not None and answer.key == current.key))
                    else set()) | set(new_shown)
            label = self._title(answer, language) if answer is not None and link else ""
            return {
                "text": text, "link": link, "link_label": label, "kind": kind,
                "answer_key": answer.key if answer is not None else None,
                "chips": chips or [],
                "context": {"key": key, "shown": sorted(seen)[:40]} if key else {},
                "meta": {"in_context": current is not None, **(meta or {})},
            }

        def more_chip(answer, seen):
            page_id = getattr(answer, "page_id", None)
            if not options["page_text"] or not page_id:
                return []
            left = [p for p in self._page_passages(page_id, language) if p.id not in seen]
            return [{"type": "more", "label": talk.text("more", language)}] if left else []

        def summary_ids(answer):
            """Passages that only repeat the answer's own text count as shown."""
            page_id = getattr(answer, "page_id", None)
            if not page_id:
                return set()
            said = self._normalize_text(answer.answer_in(language))[:200]
            if not said:
                return set()
            return {p.id for p in self._page_passages(page_id, language)
                    if self._normalize_text(p.text)[:200] in said or said in self._normalize_text(p.text)}

        def page_answer(answer, kind, meta, vectors=None, query_text=""):
            """The answer's text, plus the paragraph of its page that best fits
            the question when that adds something."""
            text = answer.answer_in(language)
            seen = summary_ids(answer)
            page_id = getattr(answer, "page_id", None)
            if options["page_text"] and page_id and vectors is not None:
                ranked = self._rank_passages(vectors, query_text, language, page_id, exclude=shown | seen)
                if ranked and ranked[0][0] >= self.EXTRA_MIN and ranked[0][1] >= 1:
                    text = f"{text}\n\n{ranked[0][2].text}"
                    seen.add(ranked[0][2].id)
                    meta = {**meta, "passage": ranked[0][2].id, "passage_score": round(ranked[0][0], 4)}
            chips = more_chip(answer, shown | seen)
            if options["related"] and answer.kind in self.PAGE_KINDS:
                chips += self._related(answer.key, language, limit=2 - min(1, len(chips)))
            for follow_up in getattr(answer, "follow_ups", []) or []:
                chips.append({"type": "ask", "label": follow_up})
            if talk.asks_price(query_text):
                chips += contact_chip()
            return result(kind, text, answer, answer.link, chips[:4], seen, meta)

        def passage_answer(passage, score, kind):
            answer = self._answers.get(self._page_answer.get(passage.page_id, ""))
            seen = {passage.id}
            if answer is None:  # a page without its own answer: quote the paragraph only
                return result(kind, passage.text, None, "", contact_chip() if talk.asks_price(query) else [],
                              seen, {"passage": passage.id, "passage_score": round(score, 4)})
            out = result(kind, passage.text, answer, answer.link, [], seen,
                         {"passage": passage.id, "passage_score": round(score, 4)})
            out["context"]["shown"] = sorted((shown if (current and current.key == answer.key) else set()) | seen)[:40]
            chips = more_chip(answer, set(out["context"]["shown"]))
            if talk.asks_price(query):
                chips += contact_chip()
            out["chips"] = chips
            return out

        if key and str(key) in self._answers:
            chosen = self._answers[str(key)]
            return page_answer(chosen, "entry" if chosen.kind == "entry" else "page", {"best_score": 1.0, "picked": True})

        if not (query or "").strip() or self._embeddings is None:
            return result("fallback", "", chips=contact_chip())

        # 1. "Dimmi di più": the next paragraphs of the page being discussed.
        if current is not None and current_page and talk.is_more(query):
            page_id = current_page
            left = [p for p in self._page_passages(page_id, language) if p.id not in shown] if page_id else []
            if left:
                taken = left[:1] if len(left[0].text) > 260 or len(left) == 1 else left[:2]
                text = "\n\n".join(p.text for p in taken)
                out = result("more", text, current, current.link, [], [p.id for p in taken], keep_context=True)
                out["chips"] = more_chip(current, set(out["context"]["shown"]))
                return out
            return result("more", talk.text("no_more", language, title=self._title(current, language)),
                          current, current.link, contact_chip(), keep_context=True)

        kind = classify(query, self._vocabulary, self._known)
        if kind in ("greeting", "thanks"):
            return result(kind, "", meta={"special": kind}, keep_context=True)
        if kind == "unclear" and current is None:
            return result("unclear", "", meta={"special": "unclear"})

        vector = self._encode(query)
        _, meta = self.answer_with_scores(query, vector=vector) if kind != "unclear" else ("", {"used_fallback": True})
        chosen = None if meta.get("used_fallback") or meta.get("special") else self._answers.get(meta.get("answer_key"))
        score_meta = {k: meta.get(k) for k in ("best_score", "margin", "matched_question", "reason") if k in meta}

        # 2. A clear answer.
        if chosen is not None:
            if current is not None and chosen.key == current.key and current_page and options["page_text"]:
                # Same subject again, more precisely: the paragraph that answers.
                ranked = self._rank_passages([vector], query, language, current_page, exclude=shown | summary_ids(current))
                if ranked and ranked[0][0] >= self.CONTEXT_MIN:
                    return passage_answer(ranked[0][2], ranked[0][0], "context")
            return page_answer(chosen, "entry" if chosen.kind == "entry" else "page", score_meta, [vector], query)

        # 3. A follow-up about the page being discussed ("e quanto dura la batteria?").
        if current is not None:
            title = self._title(current, "it")
            combined = self._encode(f"{query} {title}")
            if current_page and options["page_text"]:
                ranked = self._rank_passages([vector, combined], query, language, current_page, exclude=shown)
                if ranked and ranked[0][0] >= self.CONTEXT_MIN and (ranked[0][1] >= 1 or talk.short_follow_up(query)):
                    if talk.asks_price(query) and ranked[0][1] == 0:
                        return result("context", talk.text("price", language), current, current.link,
                                      contact_chip(), keep_context=True)
                    return passage_answer(ranked[0][2], ranked[0][0], "context")
            if talk.asks_price(query):
                return result("context", talk.text("price", language), current, current.link,
                              contact_chip(), keep_context=True)
            _, again = self.answer_with_scores(f"{query} {title}", vector=combined)
            other = None if again.get("used_fallback") or again.get("special") else self._answers.get(again.get("answer_key"))
            if other is not None:
                return page_answer(other, "context", {**score_meta, "with_context": True}, [combined], query)
            if kind == "unclear":
                return result("unclear", "", meta={"special": "unclear"}, keep_context=True)

        # 4. A paragraph somewhere on the site.
        if options["page_text"]:
            ranked = self._rank_passages([vector], query, language)
            if ranked:
                score, common, passage = ranked[0]
                same_language = passage.language == language
                if score >= self.PASSAGE_MIN and (common >= 1 or (not same_language and score >= self.PASSAGE_MIN + 0.08)):
                    return passage_answer(passage, score, "passage")

        # 5. Two answers equally close: ask which one.
        ranking = [(k, v) for k, v in self._answer_ranking(vector) if k in self._answers]
        close = [(k, v) for k, v in ranking[:3] if v >= self.CLARIFY_MIN and ranking[0][1] - v < self.MARGIN]
        if len(close) >= 2:
            first, second = (self._answers[k] for k, _ in close[:2])
            if self._title(first, language).lower() != self._title(second, language).lower():
                text = talk.text("clarify", language, a=self._title(first, language), b=self._title(second, language)) \
                    if len(close) == 2 else talk.text("clarify_many", language)
                chips = [{"type": "ask", "label": self._title(self._answers[k], language), "key": k} for k, _ in close]
                return result("clarify", text, chips=chips, meta=score_meta, keep_context=True)

        # 6. Nothing close enough.
        if talk.asks_price(query):
            return result("fallback", talk.text("price", language), chips=contact_chip(), meta=score_meta,
                          keep_context=True)
        return result("fallback", "", chips=contact_chip(), meta=score_meta, keep_context=True)

    def site_answers(self):
        """The answers built from the site (for evaluate_chatbot)."""
        self._ensure_loaded()
        return [a for a in self._answers.values() if a.kind != "entry"]


engine = ChatbotEngine()
