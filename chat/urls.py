from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('new/', views.chat_session, name='new_chat'),
    path('session/<int:session_id>/', views.chat_session, name='chat_session'),
    path('session/<int:session_id>/send/', views.send_message, name='send_message'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/rename/', views.rename_session, name='rename_session'),
]
