"""
Blocks only the Soluzioni pages have: the two sections the site used to add
by itself after the content ("Come lavoriamo" and "Altre soluzioni").

Put one of these blocks in the page content to choose WHERE that section
appears; other blocks can go before or after it. Without the block, the
section appears after the content as before (switches in the Meta panel:
"Mostra 'Come lavoriamo'" / "Mostra 'Altre soluzioni'").
"""
from wagtail import blocks

from core.blocks_solutions import StepItemBlock


class ProcessStepsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(
        max_length=120, required=False, label="Titolo",
        help_text="Vuoto = 'Come lavoriamo' (tradotto da solo in inglese e francese).",
    )
    steps = blocks.ListBlock(
        StepItemBlock(), required=False, default=[], label="Passaggi",
        help_text="Vuoto = i 5 passaggi di Axatel (Programmiamo, Installiamo, Raccogliamo, "
                  "Analizziamo, Automatizziamo), già tradotti. Aggiungi passaggi solo per "
                  "scriverne di diversi per questa pagina.",
    )

    class Meta:
        icon = "list-ol"
        label = "Come lavoriamo"


class RelatedSolutionsBlock(blocks.StructBlock):
    heading = blocks.CharBlock(
        max_length=120, required=False, label="Titolo",
        help_text="Vuoto = 'Altre soluzioni'. Le card sono scelte da sole: "
                  "fino a 4 altre soluzioni, prima quelle dello stesso gruppo.",
    )

    class Meta:
        icon = "list-ul"
        label = "Altre soluzioni"


SOLUTION_SECTION_BLOCKS = [
    ("process_steps", ProcessStepsBlock()),
    ("related_solutions", RelatedSolutionsBlock()),
]
