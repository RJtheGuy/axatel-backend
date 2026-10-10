"""
Words and sentences of a conversation with the chatbot, in Italian, English
and French: "tell me more", short follow-ups ("e quanto costa?"), prices,
and the fixed texts of the buttons under an answer.

Kept apart from engine.py so the rules can be read (and extended) without
touching the matching.
"""
from __future__ import annotations

import re

from .understanding import STOPWORDS, plain, words

# "Dimmi di più", "altro?", "tell me more", "plus de détails"…: continue
# with the page the conversation is about.
MORE_PATTERNS = [
    r"^(e )?(dimmi|raccontami|spiegami|parlami)( pure| un po'?)? (di )?(piu|meglio|altro|ancora)\b",
    r"^(dimmi|dammi|voglio|vorrei)( altri| piu| maggiori)? (dettagli|informazioni|info)\b",
    r"^(altro|ancora|continua|prosegui|vai avanti|e poi|di piu|piu dettagli|maggiori dettagli|"
    r"maggiori informazioni|altre informazioni|approfondisci|approfondimento|piu info|altre info)$",
    r"^(tell me|show me)( some)? more\b", r"^(more|more info|more details|go on|continue|anything else|and then)$",
    r"^(dites|dis)[- ]?(m|moi)[ '-]?(en )?plus\b", r"^(plus de details|encore|continuez|continue|et ensuite|et apres)$",
]
_MORE = [re.compile(p) for p in MORE_PATTERNS]

# Words that ask about prices and offers: the answer gets the contact button.
PRICE_WORDS = {
    "prezzo", "prezzi", "costo", "costi", "costa", "costano", "preventivo", "preventivi", "offerta",
    "listino", "tariffa", "tariffe", "quotazione", "noleggio", "acquistare", "comprare",
    "price", "prices", "cost", "costs", "quote", "pricing", "buy", "purchase",
    "prix", "tarif", "tarifs", "devis", "acheter", "coute", "coutent",
}

# Question words and words found everywhere on this site: they say nothing
# about *which* paragraph answers, so they are left out of the word match.
GENERIC = STOPWORDS | set("""
come cosa cose quale quali quanto quanta quanti quante dove quando perche chi fate avete usate potete
siete sono posso puoi servono serve funziona funzionano fare fanno essere stato stata viene vengono
anche molto tutto tutti tutte ogni altro altra altri altre ancora dimmi spiegami raccontami vorrei
voglio sapere qualcosa informazioni info dettagli
axatel sistema sistemi soluzione soluzioni monitoraggio monitorare monitorate monitorate monitora
how what which where when why who does have used using can could would should about tell more
system systems solution solutions monitoring monitor
comment quoi quel quelle quels quelles pourquoi est sont avez utilisez faites peut pouvez systeme
systemes surveillance surveiller
""".split())

TEXTS = {
    "more": {"it": "Dimmi di più", "en": "Tell me more", "fr": "Dites-m'en plus"},
    "contact": {"it": "Parla con un esperto", "en": "Talk to an expert", "fr": "Parler à un expert"},
    "clarify": {"it": "Intendi {a} o {b}?", "en": "Do you mean {a} or {b}?", "fr": "Vous parlez de {a} ou de {b} ?"},
    "clarify_many": {"it": "Di quale di questi vuoi sapere?", "en": "Which of these would you like to know about?",
                     "fr": "Lequel de ces sujets vous intéresse ?"},
    "no_more": {
        "it": "Su {title} ti ho detto quello che trovi nel sito. Per i dettagli del tuo caso, parla con un nostro esperto.",
        "en": "That is what the site says about {title}. For the details of your case, talk to one of our experts.",
        "fr": "C'est ce que le site dit sur {title}. Pour les détails de votre cas, parlez à l'un de nos experts.",
    },
    "price": {
        "it": "Il costo dipende dal progetto (sensori, punti di misura, installazione e servizi): prepariamo un "
              "preventivo su misura.",
        "en": "The cost depends on the project (sensors, measuring points, installation and services): we prepare "
              "a tailored quote.",
        "fr": "Le coût dépend du projet (capteurs, points de mesure, installation et services) : nous préparons "
              "un devis sur mesure.",
    },
}


def text(name: str, language: str, **values) -> str:
    template = TEXTS[name].get(language) or TEXTS[name]["it"]
    return template.format(**values) if values else template


def is_more(question: str) -> bool:
    """ "Dimmi di più", "altro?", "tell me more"… """
    cleaned = " ".join(words(question))
    return any(p.search(cleaned) for p in _MORE)


def asks_price(question: str) -> bool:
    return any(w in PRICE_WORDS for w in words(question))


def _stem(word: str) -> str:
    return word[:5]


def content_stems(value: str) -> set[str]:
    """The words that carry the subject, cut to a stem (sensore/sensori → senso)."""
    return {_stem(w) for w in words(value) if len(w) >= 4 and w not in GENERIC}


def overlap(question: str, passage_text: str) -> int:
    return len(content_stems(question) & content_stems(passage_text))


def short_follow_up(question: str) -> bool:
    """ "e per i ponti?", "quanto costa?", "and the battery?": few words, maybe
    starting with "e" / "and" / "et". Only a hint: the engine still decides. """
    tokens = words(question)
    return 0 < len(tokens) <= 6 or plain(question).strip().startswith(("e ", "and ", "et ", "ma ", "but "))
