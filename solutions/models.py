from core.base_pages import CardSectionIndexPage, CardDetailPage
 
 
class SolutionsIndexPage(CardSectionIndexPage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["solutions.SolutionPage"]
 
    class Meta:
        verbose_name = "Indice Soluzioni"
 
 
class SolutionPage(CardDetailPage):
    parent_page_types = ["solutions.SolutionsIndexPage"]
    subpage_types = []
 
    class Meta:
        verbose_name = "Soluzione"
        verbose_name_plural = "Soluzioni"