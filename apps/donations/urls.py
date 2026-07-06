from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('donations/create/', views.donation_create_view, name='donation_create'),
    path('donations/<int:pk>/edit/', views.donation_update_view, name='donation_update'),
    path('donations/<int:pk>/delete/', views.donation_delete_view, name='donation_delete'),
    path('donations/export/', views.export_csv_view, name='export_csv'),
]
