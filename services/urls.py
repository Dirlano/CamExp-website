from django.urls import path
from . import views

app_name = 'services'

urlpatterns = [
    # Main service listing
    path('', views.list_services, name='list'),
    
    # Other URL patterns...
    path('search/', views.search, name='search'),
    path('create/', views.create_listing, name='create_listing'),
    path('rate/<int:expert_id>/', views.rate_expert, name='rate_expert'),
    path('detail/<int:id>/', views.service_detail, name='service_detail'),
    path('request/create/', views.create_request, name='create_request'),
    path('request/<int:id>/respond/', views.respond_request, name='respond_request'),
    path('react/<int:post_id>/', views.react_post, name='react_post'),
    
    # API endpoints
    path('api/subcategories/', views.get_subcategories, name='get_subcategories'),
    path('api/favorite/<int:service_id>/', views.toggle_favorite, name='toggle_favorite'),
]