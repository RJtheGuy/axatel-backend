from django.urls import path
from . import views  
urlpatterns = [
    path("ask/", views.chat, name="chatbot-chat"),
]