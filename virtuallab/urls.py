from django.urls import path

from . import views


app_name = "virtuallab"


urlpatterns = [
    path(
        "",
        views.lab_catalog,
        name="lab_catalog",
    ),

    path(
        "request/<int:lab_id>/",
        views.request_lab_access,
        name="request_lab_access",
    ),

    path(
        "manage/",
        views.lab_management,
        name="lab_management",
    ),


    path(
        "manage/lab/<int:lab_id>/toggle-status/",
        views.toggle_lab_status,
        name="toggle_lab_status",
    ),


    path(
        "manage/lab/create/",
        views.create_lab,
        name="create_lab",
    ),

    path(
        "my-requests/",
        views.my_lab_requests,
        name="my_lab_requests",
    ),

    path(
        "access-requests/",
        views.access_requests,
        name="access_requests",
    ),

    path(
        "access-requests/lab/<int:lab_id>/",
        views.lab_access_details,
        name="lab_access_details",
    ),

    path(
        "access-requests/<int:request_id>/toggle-student-access/",
        views.toggle_student_lab_access,
        name="toggle_student_lab_access",
    ),

    path(
        "access-requests/<int:request_id>/approve/",
        views.approve_access_request,
        name="approve_access_request",
    ),

    path(
        "access-requests/<int:request_id>/reject/",
        views.reject_access_request,
        name="reject_access_request",
    ),

    path(
        "lab/<int:lab_id>/open/",
        views.lab_overview,
        name="lab_overview",
    ),

    path(
        "manage/lab/<int:lab_id>/",
        views.lab_manager_overview,
        name="lab_manager_overview",
    ),

    path(
        "lab/<int:lab_id>/session/",
        views.lab_session,
        name="lab_session",
    ),

    path(
        "lab/<int:lab_id>/assignments/",
        views.lab_assignments,
        name="lab_assignments",
    ),

    path(
        "lab/<int:lab_id>/terminal-page/",
        views.terminal,
        name="terminal",
    ),

    path(
        "lab/<int:lab_id>/file-manager/",
        views.file_manager,
        name="file_manager",
    ),

    path(
        "lab/<int:lab_id>/access/",
        views.access_lab,
        name="access_lab",
    ),

    path(
        "manage/lab/<int:lab_id>/edit/",
        views.edit_lab,
        name="edit_lab",
    ),

    path(
        "lab/<int:lab_id>/file/create/",
        views.create_workspace_file,
        name="create_workspace_file",
    ),
    path(
        "lab/<int:lab_id>/folder/create/",
        views.create_workspace_folder,
        name="create_workspace_folder",
    ),

    path(
        "lab/<int:lab_id>/file/delete/",
        views.delete_workspace_item,
        name="delete_workspace_item",
    ),

    path(
        "lab/<int:lab_id>/file/rename/",
        views.rename_workspace_item,
        name="rename_workspace_item",
    ),

    path(
        "lab/<int:lab_id>/files/",
        views.workspace_files,
        name="workspace_files",
    ),

    path(
        "lab/<int:lab_id>/file/upload/",
        views.upload_workspace_file,
        name="upload_workspace_file",
    ),

    path(
        "lab/<int:lab_id>/file/",
        views.workspace_file,
        name="workspace_file",
    ),

    path(
        "lab/<int:lab_id>/file/content/",
        views.workspace_file_content,
        name="workspace_file_content",
    ),

    path(
        "lab/<int:lab_id>/file/save/",
        views.save_workspace_file,
        name="save_workspace_file",
    ),

    path(
        "lab/<int:lab_id>/terminal/",
        views.terminal_command,
        name="terminal_command",
    ),

    path(
        "lab/<int:lab_id>/run-code/",
        views.run_code,
        name="run_code",
    ),

        path(
        "manage/lab/<int:lab_id>/resources/",
        views.manage_lab_resources,
        name="manage_lab_resources",
    ),
    path(
        "lab/<int:lab_id>/resources/",
        views.lab_resources,
        name="lab_resources",
    ),
    path(
        "manage/lab/<int:lab_id>/resources/add/",
        views.add_lab_resource,
        name="add_lab_resource",
    ),

    path(
        "manage/resource/<int:resource_id>/delete/",
        views.delete_lab_resource,
        name="delete_lab_resource",
    ),

    path(
        "manage/docker-environments/",
        views.docker_environment_management,
        name="docker_environment_management",
    ),

    path(
        "manage/docker-environments/add/",
        views.add_docker_environment,
        name="add_docker_environment",
    ),

]