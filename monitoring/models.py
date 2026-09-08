
from core.base_pages import CardSectionIndexPage, CardDetailPage
 
 
class MonitoringIndexPage(CardSectionIndexPage):
    parent_page_types = ["home.HomePage"]
    subpage_types = ["monitoring.MonitoringPage"]
 
    class Meta:
        verbose_name = "Indice Monitoraggio"
 
 
class MonitoringPage(CardDetailPage):
    parent_page_types = ["monitoring.MonitoringIndexPage"]
    subpage_types = []
 
    class Meta:
        verbose_name = "Argomento monitoraggio"
        verbose_name_plural = "Argomenti monitoraggio"