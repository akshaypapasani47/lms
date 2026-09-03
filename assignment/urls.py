from django.urls import path
from . import views

urlpatterns = [
    path('', views.assignment_list, name='assignment_list'),
    path('create/', views.create_assignment, name='create_assignment'),
    path('<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('<int:assignment_id>/add-question/', views.add_question, name='add_question'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('question/<int:question_id>/add-testcase/', views.add_test_case, name='add_test_case'),
    path('testcase/<int:test_case_id>/edit/', views.edit_test_case, name='edit_test_case'),
    path('<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('submission/<int:submission_id>/', views.submission_result, name='submission_result'),
]