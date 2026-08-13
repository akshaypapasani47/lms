from django.urls import path
from . import views
from .consumers import TerminalConsumer
urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'login/',
        views.login_view,
        name='lab_login'
    ),

    path(
        "signup/",
        views.signup_view,
        name="signup"
    ),


    path(
        'terminal/',
        views.terminal_view,
        name='lab_terminal'
    ),

    path(
        "logout/",
        views.logout_view,
        name="lab_logout"
    ),

    path(
        "faculty-dashboard/",
        views.faculty_dashboard,
        name="faculty_dashboard"
    ),

    path("user-report/<str:username>/", views.user_report),
    path("faculty-dashboard-data/", views.faculty_dashboard_data),
    path("extend-user/<int:id>/",views.extend_lab_user,name="extend_lab_user"),
    path("reduce-user/<int:id>/",views.reduce_lab_user,name="reduce_lab_user"),
    path(
        "toggle-user/<int:id>/",
        views.toggle_lab_user,
        name="toggle_lab_user"
    ),

    path(
        "bulk-extend/",
        views.bulk_extend_users,
        name="bulk_extend_users"
    ),

    path(
        "bulk-reduce/",
        views.bulk_reduce_users,
        name="bulk_reduce_users"
    ),

    path(
        "bulk-disable/",
        views.bulk_disable_users,
        name="bulk_disable_users"
    ),

    path(
        "bulk-enable/",
        views.bulk_enable_users,
        name="bulk_enable_users"
    ),

    path(
        "set-expiry/",
        views.bulk_set_expiry,
        name="bulk_set_expiry"
    ),


    #FILE MANAGER
    path(
        "files/",
        views.files_view,
        name="files",
    ),

    path(
        "workspace/",
        views.workspace,
        name="workspace",
    ),

    path(
        "upload/",
        views.upload_file,
        name="upload_file"
    ),

    path(
        "create-folder/",
        views.create_folder,
        name="create_folder"
    ),

    path(
        "create-file/",
        views.create_file,
        name="create_file"
    ),

    path(
        "rename-item/",
        views.rename_item,
        name="rename_item"
    ),

    path(
        "delete-item/",
        views.delete_item,
        name="delete_item"
    ),

    path(
        "download-item/",
        views.download_item,
        name="download_item"
    ),

    path(
        "view-item/",
        views.view_item,
        name="view_item"
    ),

    path(
        "save-file/",
        views.save_file,
        name="save_file"
    ),

    path(
        "file-properties/",
        views.file_properties,
        name="file_properties"
    ),

    path(
        "copy-item/",
        views.copy_item,
        name="copy_item"
    ),

    path(
        "cut-item/",
        views.cut_item,
        name="cut_item"
    ),

    path(
        "paste-item/",
        views.paste_item,
        name="paste_item"
    ),

    # path(

    #     "run-command/",
    #     views.run_command,
    #     name="run_command"
    # ),

    

]
