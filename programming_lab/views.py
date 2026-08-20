from django.shortcuts import render, redirect, get_object_or_404
from .models import ProgrammingLab
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages

import os
from django.conf import settings
import re
from django.http import FileResponse



from django.contrib import messages

from .services.workspace_service import(

    start_workspace,
    stop_workspace,
    restart_workspace

)

import tempfile
import subprocess
import shutil
import zipfile
from datetime import datetime

from .docker_manager import (
    create_container,
    get_container_status,
    start_container,
    stop_container,
    restart_container,
    delete_container,
)

from .models import StudentContainer
from .utils import get_safe_username
from .models import VirtualLab, VirtualLabAccess
from django.contrib.auth import get_user_model

User = get_user_model()



# def start_lab(request):

#     response=start_workspace()


#     request.session["workspace_status"]=response[
#         "workspace_status"
#     ]


#     request.session["container_status"]=response[
#         "container_status"
#     ]


#     messages.success(

#         request,

#         response["message"]

#     )


#     return redirect(

#         "programming_terminal"

#     )

# def stop_lab(request):

#     response=stop_workspace()


#     request.session["workspace_status"]=response[
#         "workspace_status"
#     ]


#     request.session["container_status"]=response[
#         "container_status"
#     ]


#     messages.success(

#         request,

#         response["message"]

#     )


#     return redirect(

#         "programming_terminal"

#     )



# def restart_lab(request):

#     response=restart_workspace()


#     request.session["workspace_status"]=response[
#         "workspace_status"
#     ]


#     request.session["container_status"]=response[
#         "container_status"
#     ]


#     messages.success(

#         request,

#         response["message"]

#     )


#     return redirect(

#         "programming_terminal"

#     )

def programming_home(request):

    labs = VirtualLab.objects.all().order_by("-created_at")

    for lab in labs:

        if request.user.is_superuser or request.user.is_lecturer:

            lab.user_has_access = True

        else:

            lab.user_has_access = VirtualLabAccess.objects.filter(
                lab=lab,
                student=request.user,
                is_active=True
            ).exists()

    context = {
        "labs": labs,
    }

    return render(
        request,
        "programming_lab/home.html",
        context
    )


# def programming_workspace(request):

#     lab = ProgrammingLab.objects.filter(
#         created_by=request.user
#     ).last()

#     container = StudentContainer.objects.filter(
#         user=request.user
#     ).first()

#     if container:
#         container_status = container.status.upper()
#     else:
#         container_status = "NOT CREATED"

#     context = {

#         "language":
#         lab.language if lab else "--",

#         "status":
#         lab.status if lab else "--",

#         "expiry":
#         lab.expiry_date if lab else "--",

#         "ram":
#         lab.allocated_ram if lab else "--",

#         "storage":
#         lab.allocated_storage if lab else "--",

#         # Docker
#         "container_status": container_status,

#     }

#     return render(
#         request,
#         "programming_lab/workspace.html",
#         context
#     )


# def programming_workspace(request):

#     lab=ProgrammingLab.objects.filter(
#         created_by=request.user
#     ).last()


#     # if not request.session.get(
#     #     "workspace_created"
#     # ):

#     #     return redirect(
#     #         "programming_home"
#     #     )


#     # lab = request.session.get(
#     #     "programming_lab",
#     #     {}
#     # )


#     context={

#         "language":
#         lab.language if lab else "--",

#         "status":
#         lab.status if lab else "--",

#         "expiry":
#         lab.expiry_date if lab else "--",

#         "ram":
#         lab.allocated_ram if lab else "--",

#         "storage":
#         lab.allocated_storage if lab else "--",

#     }

#     return render(
#         request,
#         "programming_lab/workspace.html",
#         context

#     )
    


# def select_language(request,language):

#     request.session["programming_lab"]={

#     "language":language.upper(),
#     "status":"ACTIVE",
#     "expiry":"Not Started",
#     "ram":"--",
#     "storage":"--"

#     }

#     request.session["workspace_created"]=True

#     return redirect(
#         "programming_workspace"
#     )


def programming_workspace(request):

    virtual_lab_id = request.session.get(
        "virtual_lab_id"
    )

    virtual_lab = None

    if virtual_lab_id:

        virtual_lab = VirtualLab.objects.filter(
            id=virtual_lab_id,
            lab_type="PROGRAMMING",
            status="ACTIVE"
        ).first()

    lab = ProgrammingLab.objects.filter(
        created_by=request.user
    ).last()


    container = StudentContainer.objects.filter(
        user=request.user,
        virtual_lab=virtual_lab
    ).first()

    # -----------------------------------------
    # Check actual Docker status
    # -----------------------------------------

    if container:

        docker_status = get_container_status(
            container.container_id
        )

        if docker_status == "RUNNING":

            container.status = "running"

            container.save(
                update_fields=["status"]
            )

            container_status = "RUNNING"

        elif docker_status == "STOPPED":

            container.status = "stopped"

            container.save(
                update_fields=["status"]
            )

            container_status = "STOPPED"

        elif docker_status == "NOT_FOUND":

            container.delete()

            container_status = "NOT CREATED"

    else:

        container_status = "NOT CREATED"

    context = {

        "virtual_lab": virtual_lab,

        "language":
        lab.language if lab else "--",

        "status":
        lab.status if lab else "--",

        "expiry":
        lab.expiry_date if lab else "--",

        "ram":
        lab.allocated_ram if lab else "--",

        "storage":
        lab.allocated_storage if lab else "--",

        "container_status":
        container_status,

        "output": request.session.get(
            "output",
            "No Program Executed Yet."
        ),

    }

    return render(
        request,
        "programming_lab/workspace.html",
        context
    )




def programming_logout(request):

    request.session.pop(
        "programming_lab",
        None
    )

    request.session.pop(
        "workspace_created",
        None
    )


    return redirect(
        "programming_home"
    )


# def create_workspace(request):

#     return render(
#         request,
#         "programming_lab/create_workspace.html"
#     )

def create_workspace(request):


    if request.method=="POST":


        language=request.POST.get(

            "language"

        )


        ram=request.POST.get(

            "ram"

        )


        storage=request.POST.get(

            "storage"

        )


        expiry=request.POST.get(

            "expiry"

        )


        ProgrammingLab.objects.create(

            language=language,

            allocated_ram=int(ram),

            allocated_storage=int(storage),

            status="ACTIVE",

            expiry_date=

            timezone.now()

            +

            timedelta(

                days=int(expiry)

            ),

            created_by=request.user

        )


        messages.success(

            request,

            "Programming Workspace Created Successfully."

        )


        return redirect(

            "programming_workspace"

        )


    return render(

        request,

        "programming_lab/create_workspace.html"

    )


# def programming_terminal(request):

#     context={

#         "workspace_status":
#         request.session.get(
#             "workspace_status",
#             "NOT STARTED"
#         ),

#         "container_status":
#         request.session.get(
#             "container_status",
#             "STOPPED"
#         ),


#         "language":
#         request.session.get(
#             "language",
#             "--"
#         ),

#         "output":
#         request.session.get(
#             "output",
#             "No Program Executed Yet."
#         ),


#         "cpu":"--",
#         "ram":"--",
#         "storage":"--",
#         "expiry":"--",
#         "container_id":"--",

#     }

#     return render(
#         request,
#         "programming_lab/programming_terminal.html",
#         context
#     )


# def programming_terminal(request):

#     container = StudentContainer.objects.filter(
#         user=request.user
#     ).first()

#     if container:

#         container_status = container.status.upper()

#         container_id = container.container_id

#     else:

#         container_status = "NOT CREATED"

#         container_id = "--"

#     context = {

#         "workspace_status":
#         request.session.get(
#             "workspace_status",
#             "NOT STARTED"
#         ),

#         "container_status":
#         container_status,

#         "language":
#         request.session.get(
#             "language",
#             "--"
#         ),

#         "output":
#         request.session.get(
#             "output",
#             "No Program Executed Yet."
#         ),

#         "cpu": "--",

#         "ram": "--",

#         "storage": "--",

#         "expiry": "--",

#         "container_id": container_id,

#     }

#     return render(
#         request,
#         "programming_lab/programming_terminal.html",
#         context
#     )



def programming_terminal(request):

    container = StudentContainer.objects.filter(
        user=request.user
    ).first()

    if container:

        docker_status = get_container_status(
            container.container_id
        )

        if docker_status == "RUNNING":

            container_status = "RUNNING"
            container_id = container.container_id

        elif docker_status == "STOPPED":

            container_status = "STOPPED"
            container_id = container.container_id

        else:

            container.delete()

            container_status = "NOT CREATED"
            container_id = "--"

    else:

        container_status = "NOT CREATED"
        container_id = "--"

    context = {

        "workspace_status":
        request.session.get(
            "workspace_status",
            "ACTIVE"
        ),

        "container_status":
        container_status,

        "language":
        request.session.get(
            "language",
            "--"
        ),

        "output":
        request.session.get(
            "output",
            "No Program Executed Yet."
        ),

        "cpu": "--",

        "ram": "--",

        "storage": "--",

        "expiry": "--",

        "container_id":
        container_id,

    }

    return render(
        request,
        "programming_lab/programming_terminal.html",
        context
    )




def file_manager(request):

    current_path=request.GET.get(
        "path",
        ""
    )

    search_query=request.GET.get(
        "search",
        ""
    ).lower()

    directory=get_student_directory(
        request,
        current_path
    )

    items=os.listdir(
        directory
    )

    files=[]

    folders=[]

    for item in items:

        item_path=os.path.join(
            directory,
            item
        )

        if os.path.isdir(
            item_path
        ):

            if (
                search_query==""
                or
                search_query in item.lower()
            ):


                folders.append(
                    item
                )


        elif os.path.isfile(
            item_path
        ):


            if (
                search_query==""
                or
                search_query in item.lower()
            ):


                file_size=os.path.getsize(
                    item_path
                )

                modified_time=os.path.getmtime(
                    item_path
                )

                files.append(

                    {
                        "name":item,
                        "size":file_size,
                        "modified":modified_time
                    }

                )

    parent_path=""

    if "/" in current_path:
        parent_path="/".join(
            current_path.split("/")[:-1]
        )


    for file in files:

        if file["size"] < 1024:

            file["display_size"]=f'{file["size"]} B'

        elif file["size"] < 1024*1024:

            file["display_size"]=f'{round(file["size"]/1024,2)} KB'

        else:

            file["display_size"]=f'{round(file["size"]/(1024*1024),2)} MB'


        file["display_modified"]=datetime.fromtimestamp(

            file["modified"]

        ).strftime(

            "%d-%b-%Y %H:%M"

        )


    context={
        "files":files,
        "folders":folders,
        "current_path":current_path,
        "parent_path":parent_path,
        "search_query":search_query
    }

    return render(

        request,

        "programming_lab/file_manager.html",

        context

    )



def get_student_directory(request, sub_path=""):

    username = get_safe_username(
        request.user.username
    )

    virtual_lab_id = request.session.get(
        "virtual_lab_id"
    )

    if not virtual_lab_id:
        raise ValueError(
            "No virtual lab selected."
        )

    virtual_lab = get_object_or_404(
        VirtualLab,
        id=virtual_lab_id
    )

    safe_lab_name = re.sub(
        r'[^a-zA-Z0-9_.-]',
        '_',
        virtual_lab.name
    ).lower()

    directory = os.path.join(
        settings.MEDIA_ROOT,
        "programming_lab",
        username,
        safe_lab_name,
        sub_path
    )

    os.makedirs(
        directory,
        exist_ok=True
    )

    return directory




# def get_student_directory(request, sub_path=""):

#     username = get_safe_username(
#         request.user.username
#     )

#     directory = os.path.join(
#         settings.MEDIA_ROOT,
#         "programming_lab",
#         username,
#         sub_path
#     )

#     os.makedirs(
#         directory,
#         exist_ok=True
#     )

#     return directory

PROGRAMMING_FILES=[

    ".py",
    ".java",
    ".cpp",
    ".c",
    ".js",
    ".html",
    ".css"
        

]


TEXT_FILES=[

    ".txt",
    ".csv",
    ".md",
    ".json",
    ".xml"
        

]


def is_programming_file(file_name):


    return any(

        file_name.endswith(extension)

        for extension in PROGRAMMING_FILES

    )


def is_text_file(file_name):


    return any(

        file_name.endswith(extension)

        for extension in TEXT_FILES

    )

def create_file(request):


    if request.method=="POST":


        file_name=request.POST.get(

            "file_name"

        )


        if file_name:


            current_path=request.POST.get(
                "current_path",
                ""
            )

            directory=get_student_directory(
                request,
                current_path
            )


            file_path=os.path.join(

                directory,

                file_name

            )


            if not os.path.exists(

                file_path

            ):


                with open(

                    file_path,

                    "w"

                ) as file:


                    file.write("")


                messages.success(

                    request,

                    "File Created Successfully."

                )


            else:


                messages.error(

                    request,

                    "File Already Exists."

                )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


def open_file(request, file_name):

    current_path=request.GET.get(
        "path",
        ""
    )

    directory=get_student_directory(
        request,
        current_path
    )

    file_path = os.path.join(

        directory,
        file_name

    )

    # if not is_text_file(file_name) and not is_programming_file(file_name):
    #     messages.warning(
    #         request,
    #         "This file cannot be edited. Please download it."
    #     )

    #     return redirect(
    #         f"/programming-lab/file-manager/?path={current_path}"
    #     )

    if not is_text_file(file_name) and not is_programming_file(file_name):

        return render(

            request,

            "programming_lab/file_not_supported.html",

            {

                "file_name":file_name,

                "current_path":current_path

            }

        )



    if os.path.exists(file_path):

        with open(

            file_path,
            "r"

        ) as file:

            content = file.read()

    else:

        content = ""

    

    context={

        "file_name":file_name,
        "content":content,
        "current_path":current_path,

        "is_programming_file":

        is_programming_file(

            file_name

        )

    }

    print(file_name)
    print(is_text_file(file_name))
    print(is_programming_file(file_name))

    return render(

        request,
        "programming_lab/open_file.html",
        context

    )


def save_file(request, file_name):

    if request.method == "POST":

        content = request.POST.get(

            "content"

        )


        current_path=request.POST.get(
            "current_path",
            ""
        )

        directory=get_student_directory(
            request,
            current_path
        )


        file_path = os.path.join(

            directory,

            file_name

        )


        with open(

            file_path,

            "w"

        ) as file:

            file.write(content)


        messages.success(

            request,

            "File Saved Successfully."

        )


    return redirect(

        f"/programming-lab/open-file/{file_name}/?path={current_path}"

    )

def rename_file(request,file_name):


    current_path=request.POST.get(

        "current_path",

        ""

    )


    if request.method=="POST":


        new_name=request.POST.get(

            "new_name"

        )


        directory=get_student_directory(

            request,

            current_path

        )


        old_path=os.path.join(

            directory,

            file_name

        )


        new_path=os.path.join(

            directory,

            new_name

        )


        if os.path.exists(

            old_path

        ):


            os.rename(

                old_path,

                new_path

            )


            messages.success(

                request,

                "File Renamed Successfully."

            )


            return redirect(

                f"/programming-lab/open-file/{new_name}/?path={current_path}"

            )


    return redirect(

        f"/programming-lab/open-file/{file_name}/?path={current_path}"

    )


def delete_file(request, file_name):


    current_path=request.GET.get(

        "path",

        ""

    )


    directory=get_student_directory(

        request,

        current_path

    )


    file_path=os.path.join(

        directory,

        file_name

    )


    if os.path.exists(

        file_path

    ):


        os.remove(

            file_path

        )


        messages.success(

            request,

            "File Deleted Successfully."

        )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )

def upload_file(request):

    current_path=""

    if request.method=="POST":

        current_path=request.POST.get(

            "current_path",

            ""

        )

        directory=get_student_directory(

            request,

            current_path

        )

        uploaded_files=request.FILES.getlist(

            "files"

        )

        for uploaded_file in uploaded_files:

            file_path=os.path.join(

                directory,

                uploaded_file.name

            )

            with open(

                file_path,

                "wb+"

            ) as destination:

                for chunk in uploaded_file.chunks():

                    destination.write(

                        chunk

                    )

        messages.success(

            request,

            f"{len(uploaded_files)} File(s) Uploaded Successfully."

        )

    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )

def download_file(request,file_name):

    directory=get_student_directory(
        request
    )

    file_path=os.path.join(

        directory,
        file_name

    )


    if os.path.exists(file_path):

        return FileResponse(

            open(
                file_path,
                "rb"
            ),

            as_attachment=True,

            filename=file_name

        )


    messages.error(

        request,

        "File Not Found."

    )


    return redirect(

        "file_manager"

    )


def run_python(file_path,user_input):


    output=""


    try:


        result=subprocess.run(

            [

                "python",
                file_path

            ],

            input=user_input,

            capture_output=True,

            text=True,

            timeout=30

        )


        output=result.stdout


        if result.stderr:

            output+=result.stderr


    except Exception as error:


        output=str(error)


    return output


def run_java(file_path,user_input):


    output=""


    try:


        directory=os.path.dirname(

            file_path

        )


        file_name=os.path.basename(

            file_path

        )


        compile_result=subprocess.run(

            [

                "javac",
                file_name

            ],

            cwd=directory,

            capture_output=True,

            text=True,

            timeout=30

        )


        if compile_result.stderr:


            return compile_result.stderr


        class_name=file_name.replace(

            ".java",

            ""

        )


        execute_result=subprocess.run(

            [

                "java",
                class_name

            ],

            input=user_input,

            cwd=directory,

            capture_output=True,

            text=True,

            timeout=30

        )


        output=execute_result.stdout


        if execute_result.stderr:


            output+=execute_result.stderr


    except Exception as error:


        output=str(error)


    return output



def run_cpp(file_path,user_input):

    output=""

    try:
        directory=os.path.dirname(
            file_path
        )

        executable_name="program.exe"
        compile_result=subprocess.run(

            [
                "g++",
                file_path,
                "-o",
                executable_name
            ],

            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30
        )

        if compile_result.stderr:
            return compile_result.stderr

        execute_result=subprocess.run(
            [
                executable_name
            ],
            input=user_input,
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=30,
            shell=True
        )

        output=execute_result.stdout

        if execute_result.stderr:
            output+=execute_result.stderr

    except Exception as error:
        output=str(error)

    return output



def run_file(request,file_name):

    output=""

    user_input=""

    if request.method=="POST":

        user_input=request.POST.get(

            "program_input",

            ""

        )

    current_path=request.GET.get(
        "path",
        ""
    )

    directory=get_student_directory(
        request,
        current_path
    )

    file_path=os.path.join(
        directory,
        file_name
    )

    if file_name.endswith(".py"):
        output=run_python(
            file_path,
            user_input
        )


    elif file_name.endswith(".java"):
        output=run_java(
            file_path,
            user_input
        )

    elif file_name.endswith(".cpp"):
        output=run_cpp(
            file_path,
            user_input
        )

    else:
        output=(
            "RUN option is currently available "
            "only for Programming Files."
        )

    request.session["output"]=output

    return redirect(
        "programming_terminal"
    )


def create_folder(request):


    if request.method=="POST":


        folder_name=request.POST.get(

            "folder_name"

        )


        if folder_name:


            current_path=request.POST.get(
                "current_path",
                ""
            )

            directory=get_student_directory(
                request,
                current_path
            )


            folder_path=os.path.join(

                directory,

                folder_name

            )


            if not os.path.exists(

                folder_path

            ):


                os.makedirs(

                    folder_path,

                    exist_ok=True

                )


                messages.success(

                    request,

                    "Folder Created Successfully."

                )


            else:


                messages.error(

                    request,

                    "Folder Already Exists."

                )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )



def delete_folder(request,folder_name):


    current_path=request.GET.get(

        "path",

        ""

    )


    directory=get_student_directory(

        request,

        current_path

    )


    folder_path=os.path.join(

        directory,

        folder_name

    )


    if os.path.exists(

        folder_path

    ):


        shutil.rmtree(

            folder_path

        )


        messages.success(

            request,

            "Folder Deleted Successfully."

        )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


def download_folder(request,folder_name):


    current_path=request.GET.get(

        "path",

        ""

    )


    directory=get_student_directory(

        request,

        current_path

    )


    folder_path=os.path.join(

        directory,

        folder_name

    )


    zip_path=os.path.join(

        directory,

        f"{folder_name}.zip"

    )


    with zipfile.ZipFile(

        zip_path,

        "w",

        zipfile.ZIP_DEFLATED

    ) as zip_file:


        for root,dirs,files in os.walk(

            folder_path

        ):


            for file in files:


                file_path=os.path.join(

                    root,

                    file

                )


                arc_name=os.path.relpath(

                    file_path,

                    folder_path

                )


                zip_file.write(

                    file_path,

                    arc_name

                )


    return FileResponse(

        open(

            zip_path,

            "rb"

        ),

        as_attachment=True,

        filename=f"{folder_name}.zip"

    )



def preview_file(request,file_name):


    current_path=request.GET.get(

        "path",

        ""

    )


    directory=get_student_directory(

        request,

        current_path

    )


    file_path=os.path.join(

        directory,

        file_name

    )


    extension=os.path.splitext(

        file_name

    )[1].lower()


    if extension==".pdf":


        return FileResponse(

            open(

                file_path,

                "rb"

            ),

            content_type="application/pdf"

        )


    elif extension in [

        ".png",

        ".jpg",

        ".jpeg",

        ".gif"

    ]:


        return render(

            request,

            "programming_lab/image_preview.html",

            {

                "file_name":file_name,

                "current_path":current_path

            }

        )


    messages.warning(

        request,

        "Preview not available for this file type."

    )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


def move_file_page(request,file_name):


    current_path=request.GET.get(

        "path",

        ""

    )


    root_directory=get_student_directory(

        request

    )


    folders=[]


    for item in os.listdir(

        root_directory

    ):


        item_path=os.path.join(

            root_directory,

            item

        )


        if os.path.isdir(

            item_path

        ):


            folders.append(

                item

            )


    context={

        "file_name":file_name,

        "folders":folders,

        "current_path":current_path

    }


    return render(

        request,

        "programming_lab/move_file.html",

        context

    )



def move_file(request,file_name):


    if request.method=="POST":


        current_path=request.POST.get(

            "current_path",

            ""

        )


        destination_folder=request.POST.get(

            "destination_folder"

        )


        source_directory=get_student_directory(

            request,

            current_path

        )


        destination_directory=get_student_directory(

            request,

            destination_folder

        )


        source_file=os.path.join(

            source_directory,

            file_name

        )


        destination_file=os.path.join(

            destination_directory,

            file_name

        )


        if os.path.exists(

            source_file

        ):


            shutil.move(

                source_file,

                destination_file

            )


            messages.success(

                request,

                "File Moved Successfully."

            )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


def copy_file_page(request,file_name):


    current_path=request.GET.get(

        "path",

        ""

    )


    root_directory=get_student_directory(

        request

    )


    folders=[]


    for item in os.listdir(

        root_directory

    ):


        item_path=os.path.join(

            root_directory,

            item

        )


        if os.path.isdir(

            item_path

        ):


            folders.append(

                item

            )


    context={

        "file_name":file_name,

        "folders":folders,

        "current_path":current_path

    }


    return render(

        request,

        "programming_lab/copy_file.html",

        context

    )

def copy_file(request,file_name):


    if request.method=="POST":


        current_path=request.POST.get(

            "current_path",

            ""

        )


        destination_folder=request.POST.get(

            "destination_folder"

        )


        source_directory=get_student_directory(

            request,

            current_path

        )


        destination_directory=get_student_directory(

            request,

            destination_folder

        )


        source_file=os.path.join(

            source_directory,

            file_name

        )


        destination_file=os.path.join(

            destination_directory,

            file_name

        )


        if os.path.exists(

            source_file

        ):


            shutil.copy2(

                source_file,

                destination_file

            )


            messages.success(

                request,

                "File Copied Successfully."

            )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )

def rename_folder_page(
    request,
    folder_name
):
    
    current_path=request.GET.get(
        "path",
        ""
    )


    return render(
        request,
        "programming_lab/rename_folder.html",
        {
            "folder_name":folder_name,
            "current_path":current_path
        }
    )


def rename_folder(
    request,
    folder_name
):


    if request.method=="POST":

        current_path=request.POST.get(
            "current_path",
            ""
        )

        new_name=request.POST.get(
            "new_name"
        )

        parent_directory=get_student_directory(
            request,
            current_path
        )

        old_folder=os.path.join(
            parent_directory,
            folder_name
        )

        new_folder=os.path.join(
            parent_directory,
            new_name
        )

        if os.path.exists(
            old_folder
        ):

            os.rename(
                old_folder,
                new_folder
            )

            messages.success(
                request,
                "Folder Renamed Successfully."
            )

    return redirect(
        f"/programming-lab/file-manager/?path={current_path}"
    )


def rename_file_page(

    request,

    file_name

):


    current_path=request.GET.get(

        "path",

        ""

    )


    return render(

        request,

        "programming_lab/rename_file.html",

        {

            "file_name":file_name,

            "current_path":current_path

        }

    )

def rename_file(

    request,

    file_name

):


    if request.method=="POST":


        current_path=request.POST.get(

            "current_path",

            ""

        )


        new_name=request.POST.get(

            "new_name"

        )


        directory=get_student_directory(

            request,

            current_path

        )


        old_file=os.path.join(

            directory,

            file_name

        )


        new_file=os.path.join(

            directory,

            new_name

        )


        if os.path.exists(

            old_file

        ):


            os.rename(

                old_file,

                new_file

            )


            messages.success(

                request,

                "File Renamed Successfully."

            )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


def upload_folder(request):


    if request.method=="POST":


        current_path=request.POST.get(

            "current_path",

            ""

        )


        directory=get_student_directory(

            request,

            current_path

        )


        uploaded_files=request.FILES.getlist(

            "folder_files"

        )


        for uploaded_file in uploaded_files:


            relative_path=uploaded_file.name


            destination_path=os.path.join(

                directory,

                relative_path

            )


            os.makedirs(

                os.path.dirname(

                    destination_path

                ),

                exist_ok=True

            )


            with open(

                destination_path,

                "wb+"

            ) as destination:


                for chunk in uploaded_file.chunks():

                    destination.write(

                        chunk

                    )


        messages.success(

            request,

            "Folder Uploaded Successfully."

        )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


def delete_selected_files(request):


    if request.method=="POST":


        current_path=request.POST.get(

            "current_path",

            ""

        )


        directory=get_student_directory(

            request,

            current_path

        )


        selected_files=request.POST.getlist(

            "selected_files"

        )


        for file_name in selected_files:


            file_path=os.path.join(

                directory,

                file_name

            )


            if os.path.exists(

                file_path

            ):


                os.remove(

                    file_path

                )


        messages.success(

            request,

            "Selected Files Deleted Successfully."

        )


    return redirect(

        f"/programming-lab/file-manager/?path={current_path}"

    )


# def start_lab(request):

#     username = request.user.username

#     student_container = StudentContainer.objects.filter(
#         user=request.user
#     ).first()

#     # User already has a container
#     if student_container:

#         # Already running
#         if student_container.status == "running":

#             messages.warning(
#                 request,
#                 "Lab is already running."
#             )

#             return redirect("file_manager")

#         # Container exists but is stopped
#         else:

#             try:

#                 start_container(
#                     student_container.container_id
#                 )

#             except:

#                 container = create_container(username)

#                 student_container.container_id = container["id"]

#                 student_container.container_name = container["name"]

#             student_container.status = "running"

#             student_container.save()

#             messages.success(
#                 request,
#                 "Lab Started Successfully."
#             )

#             return redirect("file_manager")

#     # First time -> create new container
#     container = create_container(username)

#     StudentContainer.objects.create(

#         user=request.user,

#         container_name=container["name"],

#         container_id=container["id"],

#         status="running"

#     )

#     messages.success(

#         request,

#         "Docker Lab Created Successfully."

#     )

#     return redirect("programming_workspace")




def start_lab(request):

    virtual_lab_id = request.session.get(
        "virtual_lab_id"
    )

    virtual_lab = get_object_or_404(
        VirtualLab,
        id=virtual_lab_id,
        lab_type="PROGRAMMING",
        status="ACTIVE"
    )

    username = request.user.username

    student_container = StudentContainer.objects.filter(
        user=request.user,
        virtual_lab=virtual_lab
    ).first()

    # ------------------------------------------------
    # CASE 1: Database has a container
    # ------------------------------------------------

    if student_container:

        docker_status = get_container_status(
            student_container.container_id
        )

        # Container really exists and is running
        if docker_status == "RUNNING":

            student_container.status = "running"
            student_container.save(
                update_fields=["status"]
            )

            messages.info(
                request,
                "Lab is already running."
            )

            return redirect(
                "programming_workspace"
            )

        # Container exists but is stopped
        elif docker_status == "STOPPED":

            started = start_container(
                student_container.container_id
            )

            if started:

                student_container.status = "running"

                student_container.save(
                    update_fields=["status"]
                )

                messages.success(
                    request,
                    "Lab Started Successfully."
                )

                return redirect(
                    "programming_workspace"
                )

        # Database has old/deleted Docker ID
        elif docker_status == "NOT_FOUND":

            messages.warning(
                request,
                "Previous Docker container was not found. A new lab container will be created."
            )

            student_container.delete()

    # ------------------------------------------------
    # CASE 2: Create new container
    # ------------------------------------------------

    container = create_container(
        username,
        virtual_lab
    )

    StudentContainer.objects.create(

        user=request.user,
        virtual_lab=virtual_lab,
        container_name=container["name"],
        container_id=container["id"],
        status="running"

    )

    messages.success(
        request,
        "Docker Lab Started Successfully."
    )

    return redirect(
        "programming_workspace"
    )





# def stop_lab(request):

#     container = StudentContainer.objects.get(
#         user=request.user
#     )

#     stop_container(
#         container.container_id
#     )

#     container.status = "stopped"

#     container.save()

#     messages.success(
#         request,
#         "Lab Stopped Successfully."
#     )

#     return redirect("programming_workspace")



def stop_lab(request):

    container = StudentContainer.objects.filter(
        user=request.user
    ).first()

    if not container:

        messages.warning(
            request,
            "No programming lab found."
        )

        return redirect(
            "programming_workspace"
        )

    stopped = stop_container(
        container.container_id
    )

    if stopped:

        container.status = "stopped"

        container.save(
            update_fields=["status"]
        )

        messages.success(
            request,
            "Lab Stopped Successfully."
        )

    else:

        # Docker container no longer exists
        container.delete()

        messages.warning(
            request,
            "The Docker container no longer existed. Lab record was reset."
        )

    return redirect(
        "programming_workspace"
    )




# def restart_lab(request):

#     container = StudentContainer.objects.get(
#         user=request.user
#     )

#     start_container(
#         container.container_id
#     )

#     container.status = "running"

#     container.save()

#     messages.success(
#         request,
#         "Lab Restarted Successfully."
#     )

#     return redirect("programming_workspace")




def restart_lab(request):

    container = StudentContainer.objects.filter(
        user=request.user
    ).first()

    if not container:

        messages.warning(
            request,
            "No programming lab found."
        )

        return redirect(
            "programming_workspace"
        )

    restarted = restart_container(
        container.container_id
    )

    if restarted:

        container.status = "running"

        container.save(
            update_fields=["status"]
        )

        messages.success(
            request,
            "Lab Restarted Successfully."
        )

    else:

        container.delete()

        messages.warning(
            request,
            "The Docker container was not found. Please start the lab again."
        )

    return redirect(
        "programming_workspace"
    )

# def delete_lab(request):

#     container = StudentContainer.objects.get(
#         user=request.user
#     )

#     delete_container(
#         container.container_id
#     )

#     container.delete()

#     messages.success(
#         request,
#         "Lab Deleted Successfully."
#     )

#     return redirect("programming_workspace")


def delete_lab(request):

    container = StudentContainer.objects.filter(
        user=request.user
    ).first()

    if not container:

        messages.warning(
            request,
            "No programming lab found."
        )

        return redirect(
            "programming_workspace"
        )

    delete_container(
        container.container_id
    )

    container.delete()

    messages.success(
        request,
        "Programming Lab Deleted Successfully."
    )

    return redirect(
        "programming_workspace"
    )



def has_virtual_lab_access(request, lab):

    if request.user.is_superuser:
        return True

    if request.user.is_lecturer:
        return True

    if not request.user.is_student:
        return False

    return VirtualLabAccess.objects.filter(
        lab=lab,
        student=request.user,
        is_active=True
    ).exists()

def create_virtual_lab(request):

    if request.method == "POST":

        name = request.POST.get("name")
        lab_type = request.POST.get("lab_type")
        description = request.POST.get("description")

        if not name or not lab_type:
            messages.error(
                request,
                "Lab name and lab type are required."
            )

            return redirect("create_virtual_lab")

        VirtualLab.objects.create(
            name=name,
            lab_type=lab_type,
            description=description,
            created_by=request.user,
            status="ACTIVE"
        )

        messages.success(
            request,
            "Virtual Lab created successfully."
        )

        return redirect(
            "create_virtual_lab"
        )

    return render(
        request,
        "programming_lab/create_virtual_lab.html"
    )


def virtual_lab_management(request):

    labs = VirtualLab.objects.all().order_by("-created_at")

    context = {
        "labs": labs
    }

    return render(
        request,
        "programming_lab/virtual_lab_management.html",
        context
    )

def manage_virtual_lab(request, lab_id):

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id
    )

    if request.method == "POST":

        lab.name = request.POST.get(
            "name"
        )

        lab.lab_type = request.POST.get(
            "lab_type"
        )

        lab.description = request.POST.get(
            "description"
        )

        lab.status = request.POST.get(
            "status"
        )

        lab.save()

        messages.success(
            request,
            "Virtual Lab updated successfully."
        )

        return redirect(
            "virtual_lab_management"
        )

    context = {
        "lab": lab,
        "lab_types": VirtualLab.LAB_TYPE_CHOICES
    }

    return render(
        request,
        "programming_lab/manage_virtual_lab.html",
        context
    )


def manage_virtual_lab_access(request, lab_id):

    if not (
        request.user.is_superuser
        or request.user.is_lecturer
    ):
        messages.error(
            request,
            "You do not have permission to manage virtual lab access."
        )

        return redirect("programming_home")


    lab = get_object_or_404(
        VirtualLab,
        id=lab_id
    )

    students = User.objects.filter(
        is_student=True
    ).order_by(
        "first_name",
        "last_name",
        "username"
    )

    existing_access = VirtualLabAccess.objects.filter(
        lab=lab,
        student__in=students
    )

    active_student_ids = set(
        existing_access.filter(
            is_active=True
        ).values_list(
            "student_id",
            flat=True
        )
    )

    if request.method == "POST":

        selected_student_ids = request.POST.getlist(
            "students"
        )

        selected_student_ids = set(
            int(student_id)
            for student_id in selected_student_ids
        )

        for student in students:

            access, created = VirtualLabAccess.objects.get_or_create(

                lab=lab,

                student=student,

                defaults={
                    "granted_by": request.user,
                    "is_active": student.id in selected_student_ids
                }

            )

            if not created:

                access.is_active = (
                    student.id in selected_student_ids
                )

                if access.is_active:

                    access.granted_by = request.user

                access.save(
                    update_fields=[
                        "is_active",
                        "granted_by"
                    ]
                )

        messages.success(
            request,
            "Virtual Lab access permissions updated successfully."
        )

        return redirect(
            "manage_virtual_lab_access",
            lab_id=lab.id
        )

    context = {

        "lab": lab,

        "students": students,

        "active_student_ids":
            active_student_ids

    }

    return render(
        request,
        "programming_lab/manage_virtual_lab_access.html",
        context
    )

def virtual_labs(request):

    if request.user.is_superuser or request.user.is_lecturer:

        labs = VirtualLab.objects.filter(
            status="ACTIVE"
        ).order_by("-created_at")

    else:

        labs = VirtualLab.objects.filter(
            status="ACTIVE",
            access_permissions__student=request.user,
            access_permissions__is_active=True
        ).distinct().order_by("-created_at")

    return render(
        request,
        "programming_lab/virtual_labs.html",
        {
            "labs": labs
        }
    )

# def open_virtual_lab(request, lab_id):

#     lab = get_object_or_404(
#         VirtualLab,
#         id=lab_id
#     )

#     # Lab itself is inactive
#     if lab.status != "ACTIVE":
#         messages.error(
#             request,
#             "This virtual lab is currently inactive."
#         )
#         return redirect("programming_home")

#     # Check student's permission
#     access = VirtualLabAccess.objects.filter(
#         lab=lab,
#         student=request.user,
#         is_active=True
#     ).first()

#     if not access:
#         messages.warning(
#             request,
#             "You are not assigned to use this virtual lab. Please contact your administrator or lecturer."
#         )
#         return redirect("programming_home")

#     # Optional expiry check
#     if access.expires_at:
#         if timezone.now() > access.expires_at:
#             messages.error(
#                 request,
#                 "Your access to this virtual lab has expired."
#             )
#             return redirect("programming_home")

#     return render(
#         request,
#         "programming_lab/open_virtual_lab.html",
#         {
#             "lab": lab,
#         }
#     )


def open_virtual_lab(request, lab_id):

    lab = get_object_or_404(
        VirtualLab,
        id=lab_id
    )

    # -----------------------------------------
    # 1. Check whether Virtual Lab is active
    # -----------------------------------------

    if lab.status != "ACTIVE":

        messages.error(
            request,
            "This virtual lab is currently inactive."
        )

        return redirect("programming_home")


    # -----------------------------------------
    # 2. Check Virtual Lab permission
    # -----------------------------------------

    if request.user.is_superuser or request.user.is_lecturer:

        has_access = True

    else:

        has_access = VirtualLabAccess.objects.filter(
            lab=lab,
            student=request.user,
            is_active=True
        ).exists()


    if not has_access:

        messages.warning(
            request,
            "You are not assigned to use this virtual lab."
        )

        return redirect("programming_home")


    # -----------------------------------------
    # 3. Check access expiry
    # -----------------------------------------

    access = VirtualLabAccess.objects.filter(
        lab=lab,
        student=request.user,
        is_active=True
    ).first()


    if access and access.expires_at:

        if timezone.now() > access.expires_at:

            messages.error(
                request,
                "Your access to this virtual lab has expired."
            )

            return redirect("programming_home")


    # -----------------------------------------
    # 4. Connect Virtual Lab type
    #    to the actual environment
    # -----------------------------------------

    if lab.lab_type == "PROGRAMMING":

        request.session["virtual_lab_id"] = lab.id

        return redirect(
            "programming_workspace"
        )


    # -----------------------------------------
    # 5. Other virtual lab types
    # -----------------------------------------
    # if lab.lab_type == "QUANTUM":

    #     return render(
    #         request,
    #         "programming_lab/quantum_lab.html",
    #         {
    #             "lab": lab,
    #             "lab_url": "https://qniverse.in/",
    #         },
    #     )

    if lab.lab_type == "QUANTUM":
        return render(request, "programming_lab/quantum_lab.html")



    return render(
        request,
        "programming_lab/open_virtual_lab.html",
        {
            "lab": lab
        }
    )