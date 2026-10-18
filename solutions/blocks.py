"""
Blocks of the Soluzioni pages.

    StepBlock           one step of "Come lavoriamo" (edited once, on the
                        Soluzioni index page, and shown on every solution)
    SolutionPickBlock   one card of "Altre soluzioni" on a solution page
"""
from wagtail import blocks

from core.blocks_solutions import StepItemBlock


class StepBlock(StepItemBlock):
    class Meta:
        icon = "list-ol"
        label = "Passaggio"


class SolutionPickBlock(blocks.PageChooserBlock):
    """A solution page chosen by hand. The API gives only its address (slug):
    the site shows its title and group in the visitor's language."""

    def __init__(self, **kwargs):
        super().__init__(page_type="solutions.SolutionPage", **kwargs)

    def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs.pop("page_type", None)
        return path, args, kwargs

    def get_api_representation(self, value, context=None):
        if not value or not value.live:
            return None
        return {"slug": value.slug, "title": value.title}

    class Meta:
        icon = "doc-full"
        label = "Soluzione"
