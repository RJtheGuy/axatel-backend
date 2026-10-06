"""
Does a question carry enough meaning to look for an answer?

The engine always finds the *closest* example question, even for "uff",
"boh" or "asdfgh": a language model sees some resemblance in anything, so
without this check such input got a real-looking answer. Before matching,
the question goes through these rules:

  - only greetings ("ciao", "buongiorno", "hello")  → greeting reply;
  - only thanks ("grazie", "thanks", "merci")        → thanks reply;
  - nothing but filler, symbols or 1-2 letter words → "not understood";
  - one or two meaningful words, none of which appears anywhere in what
    the chatbot knows (example questions, answers, page titles in IT, EN
    and FR, with small typos and plurals tolerated) → "not understood";
  - only keyboard mashing ("asdfgh qwerty zxcv")     → "not understood".

Everything else goes to the normal matching, where the score thresholds
still decide between an answer and the "I can only answer about Axatel"
reply. A question that is exactly one of the example questions always
passes, so a hand-written entry for "ciao" or "AI" keeps working.

The "not understood" reply is edited in Impostazioni → Chatbot.
"""
from __future__ import annotations

import re
import unicodedata

# Articles, prepositions, conjunctions, pronouns: they carry no topic.
STOPWORDS = set("""
il lo la i gli le un uno una di a da in con su per tra fra del dello della dei degli delle al allo alla ai
agli alle dal dallo dalla dai dagli dalle nel nello nella nei negli nelle col coi sul sullo sulla sui sugli
sulle e ed o od ma se che non mi ti ci vi si ne me te noi voi lui lei loro mio mia tuo tua suo sua questo
questa quello quella c ce
the an of to in on at for from by with and or but if not is are be it its this that these those my your
our their me you we they he she do does did
le la les un une des du de d l et ou mais si ne pas en au aux sur dans par pour avec ce cet cette ces je tu
il elle nous vous ils elles mon ma mes ton ta tes son sa ses
""".split())

# Interjections and filler: never a question on their own.
FILLERS = set("""
uff uffa uffi mah boh beh bah eh ehm ah ahh oh ohh uh uhm um umm mm mmm hmm hm hmmm mh lol ahah ahahah
haha hahaha hehe hihi xd ok okay okk k si no yes yep nope nah oui non bof pff pfff tss test prova
prove provo asd bla blabla niente nulla nothing rien boh boh
""".split())

GREETINGS = set("""
ciao salve buongiorno buonasera buonpomeriggio hey hi hello hola bonjour bonsoir salut coucou
""".split())

THANKS = set("""
grazie grazies grazieee mille thanks thank thx ty merci perfetto ottimo great
""".split())

VOWELS = set("aeiouy")


def plain(text: str) -> str:
    """Lowercase, accents removed: "Perché" → "perche"."""
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", plain(text))


def _mashed(word: str) -> bool:
    """Keyboard mashing: no vowel, a letter 3 times in a row, or 5 consonants in a row."""
    if not any(ch in VOWELS for ch in word):
        return True
    if re.search(r"(.)\1\1", word):
        return True
    return bool(re.search(r"[^aeiouy]{5,}", word))


def _close(a: str, b: str) -> bool:
    """At most one letter added, removed or changed (typos)."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(x != y for x, y in zip(a, b)) <= 1
    if len(a) > len(b):
        a, b = b, a
    i = 0
    while i < len(a) and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


class Vocabulary:
    """Every word the chatbot knows, from its questions and answers."""

    def __init__(self, texts):
        self.words: set[str] = set()
        for text in texts:
            self.words.update(w for w in words(text) if len(w) >= 2)
        self._by_start: dict[str, list[str]] = {}
        for word in self.words:
            if len(word) >= 4:
                self._by_start.setdefault(word[:3], []).append(word)

    def knows(self, word: str) -> bool:
        if word in self.words:
            return True
        if len(word) < 4:
            return False  # "uff" must not count as "ufficio"
        for known in self._by_start.get(word[:3], ()):
            # Same stem (sensore/sensori, monitorate/monitoraggio) or a typo.
            if len(known) >= 4 and (known[:5] == word[:5] if len(word) >= 5 else known.startswith(word) and len(known) - len(word) <= 2):
                return True
            if len(word) >= 5 and _close(word, known):
                return True
        return False


def classify(question: str, vocabulary: Vocabulary | None, known_questions: set[str] | None = None) -> str | None:
    """None when the question should be matched normally, otherwise
    "greeting", "thanks" or "unclear"."""
    if known_questions and " ".join(words(question)) in known_questions:
        return None
    tokens = words(question)
    if not tokens:
        return "unclear"
    content = [t for t in tokens if len(t) >= 3 and t not in STOPWORDS and t not in FILLERS
               and t not in GREETINGS and t not in THANKS]
    if not content:
        if any(t in GREETINGS for t in tokens):
            return "greeting"
        if any(t in THANKS for t in tokens):
            return "thanks"
        return "unclear"
    if all(_mashed(t) for t in content):
        return "unclear"
    distinct = set(content)
    if vocabulary is not None and len(distinct) <= 2 and not any(vocabulary.knows(t) for t in distinct):
        return "unclear"
    return None


REPLIES = {
    "thanks": {
        "it": "Prego! Se hai altre domande su Axatel, sono qui.",
        "en": "You're welcome! If you have other questions about Axatel, I'm here.",
        "fr": "Je vous en prie ! Si vous avez d'autres questions sur Axatel, je suis là.",
    },
    "greeting": {
        "it": "Ciao! Chiedimi pure di Axatel, dei nostri sistemi di monitoraggio o dei progetti realizzati.",
        "en": "Hi! Ask me about Axatel, our monitoring systems or our projects.",
        "fr": "Bonjour ! Posez-moi vos questions sur Axatel, nos systèmes de surveillance ou nos projets.",
    },
    "unclear": {
        "it": "Non ho capito la domanda. Puoi scriverla con qualche parola in più? Per esempio: «Come monitorate le frane?»",
        "en": "I didn't understand the question. Could you write it with a few more words? For example: \"How do you monitor landslides?\"",
        "fr": "Je n'ai pas compris la question. Pouvez-vous l'écrire avec quelques mots de plus ? Par exemple : « Comment surveillez-vous les glissements de terrain ? »",
    },
}
