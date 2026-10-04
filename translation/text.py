"""
Text handling around the translation model, independent of the model:

- split long text into sentences (the model works best sentence by sentence
  and has a length limit);
- rich text (HTML): translate only the words between tags, so links, bold
  and paragraphs stay exactly as they are;
- protected terms (product and brand names): checked after translation, and
  shielded with placeholders when the model changed them.
"""
import html
import re
from html.parser import HTMLParser

# Sentence ends: . ! ? … followed by a space and an upper-case letter,
# a digit or an opening quote/bracket. Keeps "es. Angel" together only when
# the next word is lower-case, which is the usual case in Italian.
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ0-9«\"“(])")
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]")
# Text that must not be sent to the model as is.
_SKIP = re.compile(r"^\s*(https?://\S+|www\.\S+|\S+@\S+\.\S+|[\d\s.,:;/+\-–%°()€$x×]+)\s*$", re.I)
_PLACEHOLDER = "ZXQ{}QXZ"
_PLACEHOLDER_RE = re.compile(r"Z\s*X\s*Q\s*(\d+)\s*Q\s*X\s*Z", re.I)


def needs_translation(text: str) -> bool:
    """False for empty strings, numbers, addresses and e-mails."""
    if not text or not text.strip():
        return False
    if _SKIP.match(text):
        return False
    return bool(_WORD.search(text))


def split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    return [part for part in _SENTENCE_END.split(text) if part.strip()]


# Pieces translated one at a time: sentences, and the parts of a sentence
# around a spaced dash ("Smart Road è ... — rilevamento di frane ..."). The
# model drops or garbles a dash in the middle of a sentence, so each side is
# translated on its own and the dash is put back.
_SEGMENT_BREAK = re.compile(r"((?<=[.!?…])\s+(?=[A-ZÀ-ÖØ-Þ0-9«\"“(])|\s+[—–]\s+)")


def split_segments(text: str) -> tuple[list[str], list[str]]:
    """(parts, separators): text == parts[0] + seps[0] + parts[1] + ..."""
    text = text.strip()
    if not text:
        return [], []
    tokens = _SEGMENT_BREAK.split(text)
    parts, seps = [], []
    for i, token in enumerate(tokens):
        if i % 2 == 0:
            if token.strip():
                parts.append(token.strip())
            elif seps:  # empty part: drop the separator before it
                seps.pop()
        elif parts:
            seps.append(f" {token.strip()} " if token.strip() else " ")
    return parts, seps[: max(0, len(parts) - 1)]


def join_segments(parts: list[str], seps: list[str]) -> str:
    out = ""
    for i, part in enumerate(parts):
        out += part
        if i < len(seps):
            out += seps[i]
    return out.strip()


_END_PUNCT = (".", "!", "?", "…", ":", ";")


def tidy(source: str, output: str) -> str:
    """Small clean-ups: no full stop the source did not have ("Parla con un
    esperto" → "Talk to an expert", not "...expert.")."""
    output = output.strip()
    if output.endswith(".") and not output.endswith("..") and not source.rstrip().endswith(_END_PUNCT):
        output = output[:-1].rstrip()
    return output


# Things copied exactly as written, whatever the model does: e-mail
# addresses, links, phone numbers and {placeholders}.
FIXED_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    re.compile(r"(?:https?://|www\.)[^\s<>\"']+[^\s<>\"'.,;:!?)]"),
    re.compile(r"\+?\d[\d ./-]{6,}\d"),
    re.compile(r"\{\w+\}"),
]


class Rule:
    """One thing the translation must contain: `pattern` found in the Italian
    must come out as `target` (None = exactly as written)."""

    def __init__(self, pattern, target=None, ignore_case=False):
        self.pattern = pattern
        self.target = target
        self.ignore_case = ignore_case

    def wanted(self, match_text: str) -> str:
        if self.target is None:
            return match_text
        if match_text[:1].isupper() and self.target[:1].islower():
            return self.target[:1].upper() + self.target[1:]
        return self.target

    def present(self, wanted: str, output: str) -> bool:
        return (wanted.lower() in output.lower()) if self.ignore_case else (wanted in output)


def term_rule(term: str, target: str | None = None) -> Rule:
    if target:
        pattern = re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", re.I)
        return Rule(pattern, target, ignore_case=True)
    return Rule(re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])"))


def expected(text: str, rules: list[Rule]) -> list[tuple[Rule, str]]:
    found, taken = [], []
    for rule in rules:
        for match in rule.pattern.finditer(text):
            span = match.span()
            if any(span[0] < end and start < span[1] for start, end in taken):
                continue  # inside a longer match already counted
            taken.append(span)
            found.append((rule, rule.wanted(match.group(0))))
    return found


def missing(text: str, output: str, rules: list[Rule]) -> bool:
    return any(not rule.present(wanted, output) for rule, wanted in expected(text, rules))


def protect_rules(text: str, rules: list[Rule]) -> tuple[str, dict[str, str]]:
    """Like protect(), for rules: each match becomes a placeholder that is
    later replaced by what the rule wants (the same text, or the glossary
    translation)."""
    mapping: dict[str, str] = {}
    for rule in rules:
        def swap(match, rule=rule):
            key = _PLACEHOLDER.format(len(mapping))
            mapping[key] = rule.wanted(match.group(0))
            return key
        text = rule.pattern.sub(swap, text)
    return text, mapping


def protect(text: str, terms: list[str]) -> tuple[str, dict[str, str]]:
    """Replace protected terms with placeholders the model copies unchanged."""
    mapping: dict[str, str] = {}
    # Longest first, so "Angel River" wins over "Angel".
    for term in sorted({t for t in terms if t}, key=len, reverse=True):
        pattern = re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])")
        if not pattern.search(text):
            continue
        key = _PLACEHOLDER.format(len(mapping))
        mapping[key] = term
        text = pattern.sub(key, text)
    return text, mapping


def restore(text: str, mapping: dict[str, str]) -> str | None:
    """Put the protected terms back; None if the model lost a placeholder."""
    found = set()

    def put_back(match):
        key = _PLACEHOLDER.format(match.group(1))
        found.add(key)
        return mapping.get(key, match.group(0))

    text = _PLACEHOLDER_RE.sub(put_back, text)
    return text if found == set(mapping) else None


def terms_in(text: str, terms: list[str]) -> list[str]:
    return [t for t in terms if t and re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", text)]


class _Splitter(HTMLParser):
    """Turns HTML into a list of ("tag", raw) and ("text", unescaped) parts."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        self.parts.append(("tag", self.get_starttag_text()))

    def handle_startendtag(self, tag, attrs):
        self.parts.append(("tag", self.get_starttag_text()))

    def handle_endtag(self, tag):
        self.parts.append(("tag", f"</{tag}>"))

    def handle_data(self, data):
        if self.parts and self.parts[-1][0] == "text":
            self.parts[-1] = ("text", self.parts[-1][1] + data)
        else:
            self.parts.append(("text", data))

    def handle_comment(self, data):
        self.parts.append(("tag", f"<!--{data}-->"))


_BLOCK_TAGS = {"p", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "div",
               "table", "thead", "tbody", "tr", "td", "th", "figure", "figcaption", "hr"}
_TAG_NAME = re.compile(r"</?\s*([a-zA-Z0-9]+)")
_TAG_PLACEHOLDER = "ZXT{}TXZ"
_TAG_PLACEHOLDER_RE = re.compile(r"Z\s*X\s*T\s*(\d+)\s*T\s*X\s*Z", re.I)


def _is_block(tag_text: str) -> bool:
    match = _TAG_NAME.match(tag_text)
    return bool(match and match.group(1).lower() in _BLOCK_TAGS)


def _flush(buffer, translate, out):
    """Translate one paragraph (text plus inline tags such as <b> or <a>)."""
    texts = [text for kind, text in buffer if kind == "text"]
    if not any(needs_translation(t) for t in texts):
        out.extend(text if kind == "tag" else html.escape(text, quote=False) for kind, text in buffer)
        return
    tags = [text for kind, text in buffer if kind == "tag"]
    if not tags:
        joined = "".join(texts)
        lead = joined[: len(joined) - len(joined.lstrip())]
        trail = joined[len(joined.rstrip()):]
        out.append(lead + html.escape(translate(joined.strip()), quote=False) + trail)
        return
    # Whole sentence with the inline tags as placeholders, so the model sees
    # "Il sistema ZXT0TXZ Angel River ZXT1TXZ misura..." rather than fragments.
    composed, numbered = [], {}
    for kind, text in buffer:
        if kind == "tag":
            key = _TAG_PLACEHOLDER.format(len(numbered))
            numbered[key] = text
            composed.append(f" {key} ")
        else:
            composed.append(text)
    source = re.sub(r"[ \t]{2,}", " ", "".join(composed))
    raw = "".join(text for _, text in buffer)
    lead = raw[: len(raw) - len(raw.lstrip())]
    trail = raw[len(raw.rstrip()):]
    translated = translate(source.strip())
    found = {}
    def put_back(match):
        key = _TAG_PLACEHOLDER.format(match.group(1))
        found[key] = True
        return "\x00" + key + "\x00"
    marked = _TAG_PLACEHOLDER_RE.sub(put_back, translated)
    if set(found) == set(numbered):
        pieces = marked.split("\x00")
        rebuilt = "".join(numbered[p] if p in numbered else html.escape(p, quote=False) for p in pieces)
        # Undo the spaces added around the placeholders: none right inside a
        # tag (<b>Angel River</b>), single spaces elsewhere.
        rebuilt = re.sub(r"(<(?!/)[^>]+>)\s+", r"\1", rebuilt)
        rebuilt = re.sub(r"\s+(</[^>]+>)", r"\1", rebuilt)
        rebuilt = re.sub(r"[ \t]{2,}", " ", rebuilt)
        out.append(lead + rebuilt + trail)
        return
    # The model lost a tag: translate piece by piece instead.
    for kind, text in buffer:
        if kind == "tag":
            out.append(text)
        elif needs_translation(text):
            l = text[: len(text) - len(text.lstrip())]
            t = text[len(text.rstrip()):]
            out.append(l + html.escape(translate(text.strip()), quote=False) + t)
        else:
            out.append(html.escape(text, quote=False))


def html_replace(value: str, translate) -> str:
    """Rebuild an HTML fragment with its text translated by translate(text);
    tags and attributes are kept byte for byte. Each paragraph or list item
    is translated as a whole, with inline tags (<b>, <a>...) shielded."""
    parser = _Splitter()
    parser.feed(value or "")
    parser.close()
    out: list[str] = []
    buffer: list[tuple[str, str]] = []
    for kind, text in parser.parts:
        if kind == "tag" and _is_block(text):
            _flush(buffer, translate, out)
            buffer = []
            out.append(text)
        else:
            buffer.append((kind, text))
    _flush(buffer, translate, out)
    return "".join(out)


def html_texts(value: str) -> list[str]:
    """What html_replace will ask the model to translate (for batching)."""
    asked: list[str] = []
    html_replace(value, lambda text: asked.append(text) or text)
    return asked


def looks_like_html(value: str) -> bool:
    return bool(re.search(r"<(p|h[1-6]|ul|ol|li|a|b|i|strong|em|br)\b", value or "", re.I))
