"""
The "📋 Meta" panel shared by Monitoraggio, Soluzioni, Servizi and the
informative pages (Azienda, Approfondimenti): the same idea as "Meta caso"
on the success stories, without client and date. Every field is optional;
an empty field shows nothing on the site.

    Categoria                → small label above the page title and on the card
    Immagine di copertina    → card picture, and on the page as chosen below
    Immagine nella pagina    → next to the introduction / large at the top
                               (like a success story) / not on the page
    Descrizione (card)       → text on the card (the page's existing field)
    Mostra titolo nella card → off when the picture already contains the title
    Tags                     → "#tag" list on the page (and on the card where
                               the card has room for it)
"""
from django.db import models

COVER_POSITIONS = [
    ("side", "Accanto all'introduzione"),
    ("top", "Grande, in apertura (come nei casi di successo)"),
    ("hidden", "Non mostrarla nella pagina (solo nella card)"),
]

CARD_DESCRIPTION_HELP = (
    "Testo mostrato nella card dell'elenco. "
    "Usato anche come descrizione per Google se il tab Promuovi è vuoto."
)


def category_field():
    return models.CharField(
        max_length=100, blank=True, verbose_name="Categoria",
        help_text="Etichetta mostrata sopra il titolo nella pagina e nella card, "
                  "es. 'Ambiente', 'Piattaforma', 'Azienda'. Vuoto = nessuna etichetta.",
    )


def cover_image_field():
    return models.ForeignKey(
        "wagtailimages.Image", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", verbose_name="Immagine di copertina",
    )


def cover_position_field():
    return models.CharField(
        max_length=10, choices=COVER_POSITIONS, default="side",
        verbose_name="Immagine nella pagina",
        help_text="Dove compare l'immagine di copertina nella pagina. "
                  "Nella card dell'elenco compare comunque.",
    )


def show_card_title_field():
    return models.BooleanField(
        default=True, verbose_name="Mostra titolo nella card",
        help_text="Spegni se l'immagine di copertina contiene già il titolo. "
                  "Senza immagine il titolo resta sempre visibile.",
    )
