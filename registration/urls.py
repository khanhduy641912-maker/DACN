from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('register/<str:ma_lhp>/', views.register_course, name='register_course'),
    path('cancel/<str:ma_lhp>/', views.cancel_course, name='cancel_course'),
    path('export-csv/', views.export_schedule_csv, name='export_csv'), 
]