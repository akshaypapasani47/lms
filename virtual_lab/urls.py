from django.urls import path
from . import views

urlpatterns = [
    path('', views.virtual_lab_list, name='virtual_lab_list'),
    path('lab/<int:id>/', views.lab_detail, name='lab_detail'),
    #path('ssh-test/', views.ssh_test, name='ssh_test'),

]