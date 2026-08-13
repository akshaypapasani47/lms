from django.urls import path
from . import views


urlpatterns=[

    path(
        "",
        views.programming_home,
        name="programming_home"
    ),

    # path(
    #     "select-language/<str:language>/",
    #     views.select_language,
    #     name="select_language"
    # ),

    path(
        "workspace/",
        views.programming_workspace,
        name="programming_workspace"
    ),

    path(
        "logout/",
        views.programming_logout,
        name="programming_logout"
    ),

    path(
        "create-workspace/",
        views.create_workspace,
        name="create_workspace"
    ),

    path(
        "terminal/",
        views.programming_terminal,
        name="programming_terminal"
    ),


    # path(
    #     "start-lab/",
    #     views.start_lab,
    #     name="start_lab"
    # ),

    # path(
    #     "stop-lab/",
    #     views.stop_lab,
    #     name="stop_lab"
    # ),

    # path(
    #     "restart-lab/",
    #     views.restart_lab,
    #     name="restart_lab"
    # ),

    #FILE MANAGER
    
    path(
        "file-manager/",
        views.file_manager,
        name="file_manager"
    ),

    path(
        "create-file/",
        views.create_file,
        name="create_file"
    ),

    path(
        "open-file/<str:file_name>/",
        views.open_file,
        name="open_file"
    ),

    path(
        "save-file/<str:file_name>/",
        views.save_file,
        name="save_file"
    ),

    path(
        "rename-file/<str:file_name>/",
        views.rename_file,
        name="rename_file"
    ),

    path(
        "delete-file/<str:file_name>/",
        views.delete_file,
        name="delete_file"
    ),

    path(
        "upload-file/",
        views.upload_file,
        name="upload_file"
    ),

    path(
        "download-file/<str:file_name>/",
        views.download_file,
        name="download_file"
    ),


    path(
        "run-file/<str:file_name>/",
        views.run_file,
        name="run_file"
    ),


    #folders

    path(
        "create-folder/",
        views.create_folder,
        name="create_folder"
    ),

    path(
        "delete-folder/<str:folder_name>/",
        views.delete_folder,
        name="delete_folder"
    ),

    path(
        "download-folder/<str:folder_name>/",
        views.download_folder,
        name="download_folder"
    ),

    path(
        "preview-file/<str:file_name>/",
        views.preview_file,
        name="preview_file"
    ),

    path(
        "move-file/<str:file_name>/",
        views.move_file_page,
        name="move_file_page"
    ),

    path(
        "move-file-save/<str:file_name>/",
        views.move_file,
        name="move_file"
    ),

    path(
        "copy-file/<str:file_name>/",
        views.copy_file_page,
        name="copy_file_page"
    ),

    path(
        "copy-file-save/<str:file_name>/",
        views.copy_file,
        name="copy_file"
    ),

    path(
        "rename-folder/<str:folder_name>/",
        views.rename_folder_page,
        name="rename_folder_page"
    ),

    path(
        "rename-folder-save/<str:folder_name>/",
        views.rename_folder,
        name="rename_folder"
    ),

    path(
        "rename-file-page/<str:file_name>/",
        views.rename_file_page,
        name="rename_file_page"
    ),

    path(
        "rename-file/<str:file_name>/",
        views.rename_file,
        name="rename_file"
    ),

    path(
        "upload-folder/",
        views.upload_folder,
        name="upload_folder"
    ),

    path(
        "delete-selected-files/",
        views.delete_selected_files,
        name="delete_selected_files"
    ),
    #docker

    path(

        "start-lab/",
        views.start_lab,
        name="start_lab"
    ),
    path(
        "stop-lab/",
        views.stop_lab,
        name="stop_lab"
    ),

    path(
        "restart-lab/",
        views.restart_lab,
        name="restart_lab"
    ),

    path(
        "delete-lab/",
        views.delete_lab,
        name="delete_lab"
    ),

    #virtaul labs

    path(
            "virtual-labs/",
            views.virtual_labs,
            name="virtual_labs"
        ),

    path(
        "virtual-labs/create/",
        views.create_virtual_lab,
        name="create_virtual_lab"
    ),

    path(
        "virtual-labs/manage/",
        views.virtual_lab_management,
        name="virtual_lab_management"
    ),      

    path(
        "virtual-labs/<int:lab_id>/manage/",
        views.manage_virtual_lab,
        name="manage_virtual_lab"
    ),     

    path(
        "virtual-labs/<int:lab_id>/access/",
        views.manage_virtual_lab_access,
        name="manage_virtual_lab_access"
    ),

    path(
        "virtual-labs/<int:lab_id>/open/",
        views.open_virtual_lab,
        name="open_virtual_lab"
    ),
    




]
