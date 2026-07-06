from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admins/', views.admin_list_view, name='admin_list'),
    path('admins/create/', views.admin_create_view, name='admin_create'),
    path('admins/<uuid:user_id>/delete/', views.admin_delete_view, name='admin_delete'),
]
