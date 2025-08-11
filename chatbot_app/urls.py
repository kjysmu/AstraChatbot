from . import views
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.chatbot_interface, name='chatbot_interface'),
]

urlpatterns += static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)