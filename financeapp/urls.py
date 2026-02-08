# financeapp/urls.py
from django.urls import path
from . import views

# app_name = 'financeapp'
urlpatterns = [
    path('', views.index, name='index'),
    path('budget/', views.budget, name='budget'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('delete-holding/<int:pk>/', views.delete_holding, name='delete_holding'),
    path('portfolio/update_nav/<int:holding_id>/', views.update_nav, name='update_nav'),
    path('budget/', views.budget, name='budget'),
    path('budget/<int:year>', views.budget, name='budget'),
    path('set_income/', views.set_income, name='set_income'),
    path('delete_expense/<int:pk>/', views.delete_expense, name='delete_expense')
]