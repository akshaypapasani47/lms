from django.urls import path

from . import views


urlpatterns = [

    # ======================================================
    # ASSESSMENTS
    # ======================================================

    path(
        "",
        views.assessment_list,
        name="assessment_list"
    ),

    path(
        "create/",
        views.assessment_create,
        name="assessment_create"
    ),

    path(
        "<int:pk>/",
        views.assessment_detail,
        name="assessment_detail"
    ),

    path(
        "results/<int:pk>/",
        views.assessment_results,
        name="assessment_results"
    ),

    path(
        "results/student/<int:pk>/",
        views.assessment_student_attempts,
        name="assessment_student_attempts"
    ),

    path(
        "results/submission/<int:pk>/",
        views.assessment_student_result,
        name="assessment_student_result"
    ),

    path(
        "<int:pk>/edit/",
        views.assessment_edit,
        name="assessment_edit"
    ),

    path(
        "<int:pk>/delete/",
        views.assessment_delete,
        name="assessment_delete"
    ),



    # ======================================================
    # ASSESSMENT ACCESS
    # ======================================================

    path(
        "access/available/",
        views.lecturer_assessment_access_list,
        name="lecturer_assessment_access_list"
    ),

    path(
        "access/request/<int:pk>/",
        views.assessment_request_access,
        name="assessment_request_access"
    ),

    path(
        "access/requests/",
        views.assessment_access_requests,
        name="assessment_access_requests"
    ),

    path(
        "access/request/<int:request_id>/approve/",
        views.approve_assessment_access,
        name="approve_assessment_access"
    ),

    path(
        "access/request/<int:request_id>/reject/",
        views.reject_assessment_access,
        name="reject_assessment_access"
    ),

    

    # ======================================================
    # QUESTIONS
    # ======================================================

    path(
        "<int:assessment_id>/questions/create/",
        views.question_create,
        name="question_create"
    ),

    path(
        "questions/<int:question_id>/edit/",
        views.question_edit,
        name="question_edit"
    ),

    path(
        "questions/<int:question_id>/delete/",
        views.question_delete,
        name="question_delete"
    ),

    # ======================================================
    # TEST CASES
    # ======================================================

    path(
        "questions/<int:question_id>/test-cases/create/",
        views.test_case_create,
        name="test_case_create"
    ),

    path(
        "test-cases/<int:test_case_id>/edit/",
        views.test_case_edit,
        name="test_case_edit"
    ),

    path(
        "test-cases/<int:test_case_id>/delete/",
        views.test_case_delete,
        name="test_case_delete"
    ),

    # ======================================================
    # OPTIONS
    # ======================================================

    path(
        "questions/<int:question_id>/options/",
        views.option_create,
        name="question_options"
    ),

    path(
        "options/<int:option_id>/edit/",
        views.option_edit,
        name="option_edit"
    ),

    path(
        "options/<int:option_id>/delete/",
        views.option_delete,
        name="option_delete"
    ),


    # ======================================================
    # ASSESSMENT PLACEMENTS
    # ======================================================

    path(
        "<int:assessment_id>/placements/create/",
        views.placement_create,
        name="placement_create"
    ),

    path(
        "placements/<int:placement_id>/edit/",
        views.placement_edit,
        name="placement_edit"
    ),

    path(
        "placements/<int:placement_id>/delete/",
        views.placement_delete,
        name="placement_delete"
    ),

    # ======================================================
    # STUDENT ASSESSMENT
    # ======================================================

    path(
        "student/",
        views.student_assessment_list,
        name="student_assessment_list"
    ),

    path(
        "student/<int:pk>/start/",
        views.student_assessment_start,
        name="student_assessment_start"
    ),

    path(
        "student/<int:pk>/attempt/",
        views.student_assessment_attempt,
        name="student_assessment_attempt"
    ),


    path(
        "student/autosave/",
        views.autosave_assessment_answer,
        name="autosave_assessment_answer",
    ),

    path(
        "student/result/<int:pk>/",
        views.student_assessment_result,
        name="student_assessment_result"
    ),

    path(
        "student/attempts/<int:pk>/",
        views.student_assessment_attempts,
        name="student_assessment_attempts",
    ),

    # path(
    #     "run-code/",
    #     views.run_code,
    #     name="run_code",
    # ),


    path(
        "programming/check/",
        views.check_programming_code,
        name="check_programming_code",
    ),

    path(
        "interactive/start/",
        views.interactive_code_start,
        name="interactive_code_start",
    ),

    path(
        "interactive/read/",
        views.interactive_code_read,
        name="interactive_code_read",
    ),

    path(
        "interactive/input/",
        views.interactive_code_input,
        name="interactive_code_input",
    ),

    path(
        "interactive/stop/",
        views.interactive_code_stop,
        name="interactive_code_stop",
    ),

    

    
        
    

]