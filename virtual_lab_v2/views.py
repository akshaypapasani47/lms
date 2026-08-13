from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
import paramiko
import time
from .forms import LabLoginForm
from .models import LabAccount
from .models import VirtualLabUser
from .models import ActiveSession
from django.utils import timezone
from django.db.models import Count
from django.utils.timezone import localtime
from django.contrib.auth import get_user_model
from virtual_lab_v2.models import VirtualLabUser, LabAccount
from django.utils import timezone
from datetime import datetime
from datetime import timedelta
import os
import stat
from django.contrib import messages
from django.http import FileResponse
import tempfile
import time

User = get_user_model()

ADMIN_HOST = "10.182.4.176"
ADMIN_USER = "test"
SSH_KEY = r"C:\Users\pakshaykumar\.ssh\id_ed25519"

# Create your views here.
# client = None
# channel = None

def terminal_view(request):
    print("TERMINAL VIEW CALLED")

    if "lab_username" not in request.session:
        return redirect("/virtual-lab2/login/")

    username = request.session.get("lab_username")
    #print("USERNAME =", request.session.get("lab_username"))
    lab_user = VirtualLabUser.objects.filter(
        linux_username=username
    ).first()

    days_left = (
        lab_user.expiry_date - timezone.now()
    ).days
    print("USERNAME =", username)
    print("LAB USER =", lab_user)


    current_path = request.GET.get("path", "")


    return render(
        request,
        "virtual_lab_v2/terminal.html",
        {
            "username": username,
            "lab_user": lab_user,
            "days_left": days_left,
            "current_path": current_path,
        }
    )

    # username = request.session["lab_username"]
    # password = request.session["lab_password"]

    # if client is None:

    #     self.client = paramiko.SSHClient()

    #     client.set_missing_host_key_policy(
    #         paramiko.AutoAddPolicy()
    #     )

    #     client.connect(
    #         hostname="10.182.4.176",
    #         username=username,
    #         password=password,
    #         #pkey=paramiko.Ed25519Key.from_private_key_file(SSH_KEY),
    #         look_for_keys=False,
    #         allow_agent=False
    #     )

    #     channel = client.invoke_shell()

    #     time.sleep(1)
    #     print("SSH Connected as:", username)
    

# def run_command(request):

#     # global client, channel

#     print("CHANNEL =", channel)

#     if channel is None:

#         username = request.session.get("lab_username")
#         password = request.session.get("lab_password")

#         print("Reconnecting SSH for:", username)

#         client = paramiko.SSHClient()

#         client.set_missing_host_key_policy(
#             paramiko.AutoAddPolicy()
#         )

#         client.connect(
#             hostname="10.182.4.176",
#             username=username,
#             password=password,
#             look_for_keys=False,
#             allow_agent=False
#         )

#         channel = client.invoke_shell()   

#         time.sleep(1)

#     output = ""

#     if request.method == "POST":

#         command = request.POST.get("command")

#         if command:

#             channel.send(command + "\n")

#             time.sleep(1)

#             while channel.recv_ready():

#                 output += channel.recv(4096).decode()

#     return JsonResponse({
#         "output": output
#     })


def get_admin_client():

    client = paramiko.SSHClient()

    client.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    key = paramiko.Ed25519Key.from_private_key_file(
        SSH_KEY
    )

    client.connect(
        hostname=ADMIN_HOST,
        username=ADMIN_USER,
        pkey=key,
        #password=password,
        look_for_keys=False,
        allow_agent=False
    )

    return client

def user_exists(username):

    client = get_admin_client()

    stdin, stdout, stderr = client.exec_command(
        f"id {username}"
    )

    result = stdout.read().decode()
    error = stderr.read().decode()
    print("STDOUT =", result)
    print("STDERR =", error)

    client.close()

    return bool(result)


def create_linux_user(username, password):

    client = get_admin_client()

    command = (
        f"sudo useradd -m {username} && "
        f"echo '{username}:{password}' | sudo chpasswd"
    )

    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    print("EXIT STATUS:", exit_status)
    

    print("STDOUT =")
    print(stdout.read().decode())

    print("STDERR =")
    print(stderr.read().decode())
    # print("STDOUT:")
    # print(stdout.read().decode())

    # print("STDERR:")
    # print(stderr.read().decode())
    #client.exec_command(command)

    client.close()
    return exit_status == 0

def verify_student_login(
    username,
    password
):

    try:

        client = paramiko.SSHClient()

        client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )

        client.connect(
            hostname=ADMIN_HOST,
            username=username,
            password=password
        )

        client.close()

        return True

    except:

        return False

def home(request):
    return render(
        request,
        "virtual_lab_v2/home.html"
    )

def lab_login(request):
    return render(
        request,
        "virtual_lab_v2/login.html"
    )


# def signup_view(request):

#     if request.method == "POST":

#         username = request.POST.get("username")
#         password = request.POST.get("password")

#         if user_exists(username):

#             return render(
#                 request,
#                 "virtual_lab_v2/signup.html",
#                 {"error": "User already exists"}
#             )

#         created=create_linux_user(
#             username,
#             password
#         )

        
#         print("USER CREATED =", created)
        
#         if not created:

#             return render(
#                 request,
#                 "virtual_lab_v2/signup.html",
#                 {
#                     "error": "Failed to create Linux user"
#                 }
#             )
#         return redirect("/virtual-lab2/login/")

#     return render(
#         request,
#         "virtual_lab_v2/signup.html"
#     )




def signup_view(request):

    if not request.user.is_authenticated:
        return redirect("/login/")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        # Student can have only one Linux account
        if request.user.is_student:

            existing = VirtualLabUser.objects.filter(
                user=request.user
            ).exists()

            if existing:

                return render(
                    request,
                    "virtual_lab_v2/signup.html",
                    {
                        "error":
                        "You already have a Virtual Lab account."
                    }
                )

        if user_exists(username):

            return render(
                request,
                "virtual_lab_v2/signup.html",
                {
                    "error":
                    "Linux user already exists."
                }
            )

        created = create_linux_user(
            username,
            password
        )

        if not created:

            return render(
                request,
                "virtual_lab_v2/signup.html",
                {
                    "error":
                    "Failed to create Linux user."
                }
            )

        VirtualLabUser.objects.create(
            user=request.user,
            linux_username=username
        )

        return redirect("/virtual-lab2/login/")

    return render(
        request,
        "virtual_lab_v2/signup.html"
    )





        # # Create LMS user only if not already present
        # if not User.objects.filter(username=username).exists():

        #     user = User.objects.create_user(
        #         username=username,
        #         password=password
        #     )

        # else:

        #     user = User.objects.get(username=username)

        # # Create VirtualLabUser record
        # VirtualLabUser.objects.get_or_create(
        #     user=user,
        #     defaults={
        #         "linux_username": username
        #     }
        # )

        # #Create LabAccount record
        # LabAccount.objects.get_or_create(
        #     user=user,
        #     defaults={
        #         "linux_username": username
        #     }
        # )


        # user = User.objects.create_user(
        #     username=username,
        #     password=password
        # )
        # print("DJANGO USER CREATED")
        # print(user)
        # print(user.id)
        # VirtualLabUser.objects.create(
        #     user=user,
        #     linux_username=username
        # )

        # LabAccount.objects.create(
        #     user=user,
        #     linux_username=username
        # )

        # VirtualLabUser.objects.create(
        #     #user=request.user,
        #     user=None,
        #     linux_username=username
        # )
        

        

def authenticate_linux_user(username,password):

    try:

        client = paramiko.SSHClient()

        client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )

        client.connect(
            hostname="10.182.4.176",
            #hostname=ADMIN_HOST,
            username=username,
            password=password,
            look_for_keys=False,
            allow_agent=False
        )

        client.close()

        return True

    except Exception as e:

        print("LOGIN FAILED:", e) 

        return False

def login_view(request):
    print("🔥 LOGIN VIEW HIT")
    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        print("USERNAME =", username)
        print("PASSWORD =", password)

        lab_user = VirtualLabUser.objects.filter(
            linux_username=username
        ).first()

        if lab_user and lab_user.is_disabled:

            return render(
                request,
                "virtual_lab_v2/login.html",
                {
                    "error":
                    "Account disabled by administrator."
                }
            )

        # CHECK EXPIRY FIRST
        lab_user = VirtualLabUser.objects.filter(
            linux_username=username
        ).first()

        if lab_user and timezone.now() > lab_user.expiry_date:

            return render(
                request,
                "virtual_lab_v2/login.html",
                {
                    "error": "Virtual Lab account expired. Contact administrator."
                }
            )

        result = authenticate_linux_user(
            username,
            password
        )

        print("AUTH RESULT =", result)

        if result:

            print("LOGIN SUCCESS")

            request.session["lab_username"] = username
            request.session["lab_password"] = password

            return redirect("workspace")

        print("LOGIN FAILED")

        return render(
            request,
            "virtual_lab_v2/login.html",
            {"error": "Invalid credentials"}
        )

    return render(
        request,
        "virtual_lab_v2/login.html"
    )

def lab_terminal(request):
    return render(
        request,
        "virtual_lab_v2/terminal.html"
    )


def logout_view(request):

    request.session.pop("lab_username", None)
    request.session.pop("lab_password", None)

    return redirect("/virtual-lab2/login/")


def faculty_dashboard(request):

    #sessions = ActiveSession.objects.all().order_by("-login_time")

    search = request.GET.get("search")

    if search:
        sessions = ActiveSession.objects.filter(
            username__icontains=search
        ).order_by("-login_time")
    else:
        sessions = ActiveSession.objects.all().order_by("-login_time")

    for session in sessions:
           # ===== STATUS CHECK =====

        if session.active:

            idle_seconds = (
                timezone.now()
                - session.last_activity
            ).total_seconds()

            if idle_seconds > 30:

                session.status = "idle"

            else:

                session.status = "active"

        else:

            session.status = "offline"

        # ===== DURATION CALCULATION =====
        if session.active:

            duration = (
                timezone.now()
                - session.login_time
            )

        elif session.logout_time:

            duration = (
                session.logout_time
                - session.login_time
            )

        else:

            duration = None

        if duration:

            #session.duration = str(duration).split(".")[0]
            total_seconds = int(duration.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            session.duration = (
                f"{hours:02d}h "
                f"{minutes:02d}m "
                f"{seconds:02d}s"
            )

        else:

            session.duration = "N/A"

        ref_time = session.last_activity or session.login_time

        diff = timezone.now() - ref_time

        seconds = int(diff.total_seconds())

        if seconds < 60:
            session.last_seen = f"{seconds} sec ago"

        elif seconds < 3600:
            session.last_seen = f"{seconds // 60} min ago"

        elif seconds < 86400:
            session.last_seen = f"{seconds // 3600} hr ago"

        else:
            session.last_seen = f"{seconds // 86400} day ago"

    # total_users = (
    #     ActiveSession.objects
    #     .values("username")
    #     .distinct()
    #     .count()
    # )

    total_users = VirtualLabUser.objects.count()

    active_users = (
        ActiveSession.objects
        .filter(active=True)
        .values("username")
        .distinct()
        .count()
    )

    inactive_users = total_users - active_users

    # Total duration of all completed sessions
    completed_sessions = ActiveSession.objects.filter(
        logout_time__isnull=False
    )

    total_duration_seconds = 0

    for session in completed_sessions:

        duration = (
            session.logout_time
            - session.login_time
        )

        total_duration_seconds += int(
            duration.total_seconds()
        )

    # Average duration
    if completed_sessions.count() > 0:

        avg_duration_seconds = (
            total_duration_seconds //
            completed_sessions.count()
        )

    else:

        avg_duration_seconds = 0

    avg_minutes = avg_duration_seconds // 60

    # Longest session
    longest_session = 0

    for session in completed_sessions:

        duration = (
            session.logout_time
            - session.login_time
        )

        longest_session = max(
            longest_session,
            int(duration.total_seconds())
        )

    longest_minutes = longest_session // 60

    # Most active user
    most_active_user = None

    user_sessions = {}

    for session in ActiveSession.objects.all():

        user_sessions[session.username] = (
            user_sessions.get(session.username, 0)
            + 1
        )

    if user_sessions:

        most_active_user = max(
            user_sessions,
            key=user_sessions.get
        )

    # session_stats = (
    #     ActiveSession.objects
    #     .values("username")
    #     .annotate(total_sessions=Count("id"))
    #     .order_by("-total_sessions")
    # )

    # session_stats = []
    # users = ActiveSession.objects.values("username").distinct()
    # for u in users:
    #     username = u["username"]
    #     sessions_user = ActiveSession.objects.filter(username=username)
    #     total_sessions = sessions_user.count()
    #     last_session = sessions_user.order_by("-login_time").first()
    #     if last_session:
    #         last_seen_time = (
    #             last_session.logout_time
    #             or last_session.login_time
    #         )
    #         diff = timezone.now() - last_seen_time
    #         seconds = int(diff.total_seconds())
    #         if seconds < 60:
    #             last_seen = f"{seconds} sec ago"
    #         elif seconds < 3600:
    #             last_seen = f"{seconds // 60} min ago"
    #         elif seconds < 86400:
    #             last_seen = f"{seconds // 3600} hr ago"
    #         else:
    #             last_seen = f"{seconds // 86400} day ago"
    #     else:
    #         last_seen = "N/A"
    #     session_stats.append({
    #         "username": username,
    #         "total_sessions": total_sessions,
    #         "last_seen": last_seen
    #     })


    session_stats = []

    users = VirtualLabUser.objects.all()

    for user in users:

        username = user.linux_username

        sessions_user = ActiveSession.objects.filter(
            username=username
        )

        total_sessions = sessions_user.count()

        last_session = sessions_user.order_by(
            "-login_time"
        ).first()

        if last_session:

            last_seen_time = (
                last_session.logout_time
                or last_session.login_time
            )

            diff = timezone.now() - last_seen_time

            seconds = int(
                diff.total_seconds()
            )

            if seconds < 60:
                last_seen = f"{seconds} sec ago"

            elif seconds < 3600:
                last_seen = f"{seconds // 60} min ago"

            elif seconds < 86400:
                last_seen = f"{seconds // 3600} hr ago"

            else:
                last_seen = f"{seconds // 86400} day ago"

        else:

            last_seen = "Never Logged In"

        session_stats.append({

            "username": username,

            "total_sessions": total_sessions,

            "last_seen": last_seen

        })

    lab_search = request.GET.get(
        "lab_search"
    )

    lab_users = VirtualLabUser.objects.select_related(
        "user"
    ).all()

    if lab_search:

        lab_users = lab_users.filter(
            linux_username__icontains=lab_search
        )

    lab_user_data = []

    for u in lab_users:

        days_left = (u.expiry_date - timezone.now()).days

        if days_left < 0 and not u.is_disabled:

            u.is_disabled = True
            u.save()
        # else:
        #     if u.is_disabled:

        #         u.is_disabled = False
        #         u.save()

        lab_user_data.append({
            "id": u.id,
            "lms_user": u.user.username,
            "linux_user": u.linux_username,
            "created": u.created_at,
            "expiry": u.expiry_date,
            "days_left": days_left,
            "status": "Expired" if days_left < 0 else "Active",
            "is_disabled": u.is_disabled,
        })
        

    return render(
        request,
        "virtual_lab_v2/faculty_dashboard.html",
        {
            
            "sessions": sessions,
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,

            "avg_minutes": avg_minutes,
            "longest_minutes": longest_minutes,
            "most_active_user": most_active_user,
            "session_stats": session_stats,
            "lab_users": lab_user_data,
        }       
    )

def user_report(request, username):

    sessions = ActiveSession.objects.filter(username=username)

    total_sessions = sessions.count()

    total_usage = 0
    longest = 0

    #last_login = None

    for s in sessions:

        duration = (
            (s.logout_time or timezone.now())
            - s.login_time
        )

        seconds = int(duration.total_seconds())

        total_usage += seconds
        longest = max(longest, seconds)

        #last_login = s.login_time
        last_session = sessions.order_by("-login_time").first()
        last_login = (
            last_session.login_time.strftime("%Y-%m-%d %H:%M")
            if last_session
            else "N/A"
        )

    return JsonResponse({
        "username": username,
        "total_sessions": total_sessions,
        "total_usage": f"{total_usage//3600}h {(total_usage%3600)//60}m",
        "longest_session": f"{longest//3600}h {(longest%3600)//60}m",
        "last_login": last_login
    })


def faculty_dashboard_data(request):

    sessions = ActiveSession.objects.all().order_by("-login_time")

    data = []

    for s in sessions:

        # status
        if s.active:
            status = "active"
        else:
            status = "offline"

        # duration
        if s.active:
            duration = timezone.now() - s.login_time
        elif s.logout_time:
            duration = s.logout_time - s.login_time
        else:
            duration = None

        duration_str = "N/A"

        if duration:
            sec = int(duration.total_seconds())
            duration_str = f"{sec//3600:02d}h {(sec%3600)//60:02d}m {sec%60:02d}s"

        # last seen
        last_seen = s.logout_time or s.login_time

        data.append({
            "username": s.username,
            "status": status,
            "login_time": str(s.login_time),
            "logout_time": str(s.logout_time) if s.logout_time else "--",
            "duration": duration_str,
            "last_seen": str(last_seen),
        })

    return JsonResponse({"sessions": data})


def extend_lab_user(request,id):

    if request.method == "POST":

        user = get_object_or_404(
            VirtualLabUser,
            id=id
        )

        days = int(
            request.POST.get(
                "extend_days",
                1
            )
        )

        user.expiry_date += timedelta(
            days=days
        )

        user.is_disabled = False
        user.save()

    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )

def reduce_lab_user(request,id):

    if request.method == "POST":

        user = get_object_or_404(
            VirtualLabUser,
            id=id
        )

        days = int(
            request.POST.get(
                "reduce_days",
                1
            )
        )

        new_expiry = user.expiry_date - timedelta(days=days)

        if new_expiry < timezone.now():
            new_expiry = timezone.now()

        user.expiry_date = new_expiry

        user.save()


    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )

def toggle_lab_user(request,id):

    user = VirtualLabUser.objects.get(
        id=id
    )

    user.is_disabled = not user.is_disabled

    user.save()

    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )

def bulk_extend_users(request):
    print(request.POST)

    if request.method == "POST":

        selected_users = request.POST.getlist(
            "selected_users"
        )

        days = int(
            request.POST.get("bulk_days",0)
        )
        print("DAYS =", days)
        for user_id in selected_users:

            user = VirtualLabUser.objects.get(
                id=user_id
            )

            user.expiry_date += timedelta(
                days=days
            )
            user.is_disabled = False
            user.save()

    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )

def bulk_reduce_users(request):

    if request.method == "POST":

        selected_users = request.POST.getlist(
            "selected_users"
        )

        days = int(
            request.POST.get("bulk_days", 0)
        )

        for user_id in selected_users:

            user = VirtualLabUser.objects.get(
                id=user_id
            )

            user.expiry_date -= timedelta(
                days=days
            )

            user.save()

    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )

def bulk_disable_users(request):

    if request.method == "POST":

        selected_users = request.POST.getlist(
            "selected_users"
        )

        for user_id in selected_users:

            user = VirtualLabUser.objects.get(
                id=user_id
            )

            user.is_disabled = True

            user.save()

    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )


def bulk_enable_users(request):

    if request.method == "POST":

        selected_users = request.POST.getlist(
            "selected_users"
        )

        for user_id in selected_users:

            user = VirtualLabUser.objects.get(
                id=user_id
            )

            user.is_disabled = False

            user.save()

    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )


def bulk_set_expiry(request):

    if request.method == "POST":

        selected_users = request.POST.getlist(
            "selected_users"
        )
        
        expiry_date = request.POST.get(
            "expiry_date"
        )
        print("SELECTED USERS =", selected_users)
        print("EXPIRY DATE =", expiry_date)
        if expiry_date:

            date_obj = datetime.strptime(
                expiry_date,
                "%Y-%m-%d"
            )

            aware_date = timezone.make_aware(
                date_obj
            )

            for user_id in selected_users:

                user = VirtualLabUser.objects.get(
                    id=user_id
                )

                print("BEFORE =", user.expiry_date)

                user.expiry_date = aware_date
                user.is_disabled = False
                user.save()

                print("AFTER =", user.expiry_date)
    return redirect(
        "/virtual-lab2/faculty-dashboard/"
    )


#FILE MANAGER

def workspace(request):
    return render(
        request,
        "virtual_lab_v2/workspace.html"
    )


def files_view(request):

    if "lab_username" not in request.session:
        return redirect("lab_login")

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    current_path = request.GET.get("path", "")
    print("CURRENT PATH =", current_path)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        sftp = ssh.open_sftp()

        home = f"/home/{linux_username}"

        if current_path:
            full_path = f"{home}/{current_path}"
        else:
            full_path = home

        display_path = full_path


        items = []

        def format_size(size):

            if size < 1024:
                return f"{size} B"

            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"

            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f} MB"

            else:
                return f"{size / (1024 * 1024 * 1024):.1f} GB"
            
        def format_modified(timestamp):

            modified = datetime.fromtimestamp(timestamp)

            now = datetime.now()

            diff = now - modified

            if diff.days == 0:

                return "Today " + modified.strftime("%I:%M %p")

            elif diff.days == 1:

                return "Yesterday"

            elif diff.days < 7:

                return f"{diff.days} days ago"

            elif diff.days < 30:

                weeks = diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"

            else:

                return modified.strftime("%d-%b-%Y")



        for file in sftp.listdir_attr(full_path):

            name = file.filename
            is_dir = stat.S_ISDIR(file.st_mode)

            if is_dir:
                icon = "fa-folder text-warning"

            else:

                ext = name.split(".")[-1].lower() if "." in name else ""

                if ext == "py":
                    icon = "fa-python text-success"

                elif ext in ["c", "cpp", "h"]:
                    icon = "fa-file-code text-primary"

                elif ext == "java":
                    icon = "fa-mug-hot text-danger"

                elif ext in ["html", "htm"]:
                    icon = "fa-html5 text-danger"

                elif ext == "css":
                    icon = "fa-css3-alt text-primary"

                elif ext == "js":
                    icon = "fa-js text-warning"

                elif ext == "json":
                    icon = "fa-file-code text-info"

                elif ext == "txt":
                    icon = "fa-file-lines text-secondary"

                elif ext == "pdf":
                    icon = "fa-file-pdf text-danger"

                elif ext in ["png", "jpg", "jpeg", "gif"]:
                    icon = "fa-file-image text-success"

                elif ext in ["zip", "rar", "tar", "gz"]:
                    icon = "fa-file-zipper text-warning"

                elif ext in ["mp4", "avi", "mkv"]:
                    icon = "fa-file-video text-info"

                elif ext in ["mp3", "wav"]:
                    icon = "fa-file-audio text-primary"

                else:
                    icon = "fa-file"

            items.append({

                "name": name,
                "is_dir": is_dir,
                "size": format_size(file.st_size),
                "modified": format_modified(file.st_mtime),
                "icon": icon,

            })

        sftp.close()
        ssh.close()

        parent_path = ""

        if current_path:

            parent_path = "/".join(
                current_path.split("/")[:-1]
            )
            
        print("USERNAME =", linux_username)
        print("CURRENT PATH =", current_path)
        print("HOME =", home)


        breadcrumbs = []

        if current_path:

            parts = current_path.split("/")

            temp = ""

            for part in parts:

                temp = part if temp == "" else temp + "/" + part

                breadcrumbs.append({

                    "name": part,

                    "path": temp

                })


        return render(

            request,

            "virtual_lab_v2/files.html",

            {

                "items": items,

                "linux_username": linux_username,

                "current_path": current_path,

                "parent_path": parent_path,

                "display_path": display_path,

                "breadcrumbs": breadcrumbs,

            },

        )

    except Exception as e:

        return render(

            request,

            "virtual_lab_v2/files.html",

            {

                "error": str(e),

            },

        )

def upload_file(request):

    if request.method != "POST":

        return redirect("files")

    linux_username = request.session["lab_username"]

    linux_password = request.session["lab_password"]

    current_path = request.POST.get(
        "current_path",
        ""
    )

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:

        messages.error(
            request,
            "No file selected."
        )

        return redirect(
            f"/virtual-lab2/files/?path={current_path}"
        )

    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    ssh.connect(

        hostname="10.182.4.176",

        username=linux_username,

        password=linux_password,

        look_for_keys=False,

        allow_agent=False,

    )

    sftp = ssh.open_sftp()

    remote_directory = f"/home/{linux_username}"

    if current_path:

        remote_directory += "/" + current_path

    remote_file = remote_directory + "/" + uploaded_file.name

    with sftp.open(remote_file, "wb") as destination:

        for chunk in uploaded_file.chunks():

            destination.write(chunk)

    sftp.close()

    ssh.close()

    messages.success(

        request,

        "File uploaded successfully."

    )

    return redirect(

        f"/virtual-lab2/files/?path={current_path}"

    )

def create_folder(request):

    if request.method != "POST":

        return redirect("files")

    linux_username = request.session["lab_username"]

    linux_password = request.session["lab_password"]

    current_path = request.POST.get(
        "current_path",
        ""
    )

    folder_name = request.POST.get(
        "folder_name",
        ""
    ).strip()

    if not folder_name:

        messages.error(
            request,
            "Folder name cannot be empty."
        )

        return redirect(
            f"/virtual-lab2/files/?path={current_path}"
        )

    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    try:

        ssh.connect(

            hostname="10.182.4.176",

            username=linux_username,

            password=linux_password,

            look_for_keys=False,

            allow_agent=False,

        )

        sftp = ssh.open_sftp()

        remote_path = f"/home/{linux_username}"

        if current_path:

            remote_path += "/" + current_path

        folder_path = remote_path + "/" + folder_name

        sftp.mkdir(folder_path)

        sftp.close()

        ssh.close()

        messages.success(
            request,
            "Folder created successfully."
        )

    except IOError:

        messages.error(
            request,
            "Folder already exists."
        )

    except Exception as e:

        messages.error(
            request,
            str(e)
        )

    return redirect(
        f"/virtual-lab2/files/?path={current_path}"
    )

def create_file(request):

    if request.method != "POST":

        return redirect("files")

    linux_username = request.session["lab_username"]

    linux_password = request.session["lab_password"]

    current_path = request.POST.get(
        "current_path",
        ""
    )

    file_name = request.POST.get(
        "file_name",
        ""
    ).strip()

    if not file_name:

        messages.error(
            request,
            "File name cannot be empty."
        )

        return redirect(
            f"/virtual-lab2/files/?path={current_path}"
        )

    ssh = paramiko.SSHClient()

    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    try:

        ssh.connect(

            hostname="10.182.4.176",

            username=linux_username,

            password=linux_password,

            look_for_keys=False,

            allow_agent=False,

        )

        sftp = ssh.open_sftp()

        remote_path = f"/home/{linux_username}"

        if current_path:

            remote_path += "/" + current_path

        file_path = remote_path + "/" + file_name

        with sftp.open(file_path, "w") as f:

            pass

        sftp.close()

        ssh.close()

        messages.success(
            request,
            "File created successfully."
        )

    except IOError:

        messages.error(
            request,
            "File already exists."
        )

    except Exception as e:

        messages.error(
            request,
            str(e)
        )

    return redirect(
        f"/virtual-lab2/files/?path={current_path}"
    )


def rename_item(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid Request"
            }
        )

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    old_name = request.POST.get("old_name")
    new_name = request.POST.get("new_name")
    current_path = request.POST.get("current_path", "")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    try:

        ssh.connect(

            hostname="10.182.4.176",

            username=linux_username,

            password=linux_password,

            look_for_keys=False,

            allow_agent=False,

        )

        home = f"/home/{linux_username}"

        if current_path:

            folder = f"{home}/{current_path}"

        else:

            folder = home

        command = f'mv "{folder}/{old_name}" "{folder}/{new_name}"'

        stdin, stdout, stderr = ssh.exec_command(command)

        error = stderr.read().decode()

        ssh.close()

        if error:

            return JsonResponse(

                {
                    "success": False,
                    "error": error
                }

            )

        return JsonResponse(

            {
                "success": True
            }

        )

    except Exception as e:

        return JsonResponse(

            {
                "success": False,
                "error": str(e)
            }

        )

def delete_item(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Invalid Request"
        })

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    item_name = request.POST.get("item_name")
    current_path = request.POST.get("current_path", "")
    is_dir = request.POST.get("is_dir") == "true"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(
        paramiko.AutoAddPolicy()
    )

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        home = f"/home/{linux_username}"

        if current_path:
            folder = f"{home}/{current_path}"
        else:
            folder = home

        full_path = f"{folder}/{item_name}"

        if is_dir:
            command = f'rm -rf "{full_path}"'
        else:
            command = f'rm "{full_path}"'

        stdin, stdout, stderr = ssh.exec_command(command)

        error = stderr.read().decode()

        ssh.close()

        if error:

            return JsonResponse({
                "success": False,
                "error": error
            })

        return JsonResponse({
            "success": True
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })

def download_item(request):

    if "lab_username" not in request.session:
        return redirect("lab_login")

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    file_name = request.GET.get("file_name")
    current_path = request.GET.get("current_path", "")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        sftp = ssh.open_sftp()

        home = f"/home/{linux_username}"

        if current_path:
            remote_path = f"{home}/{current_path}/{file_name}"
        else:
            remote_path = f"{home}/{file_name}"

        temp = tempfile.NamedTemporaryFile(delete=False)

        sftp.get(remote_path, temp.name)

        sftp.close()
        ssh.close()

        return FileResponse(
            open(temp.name, "rb"),
            as_attachment=True,
            filename=file_name
        )

    except Exception as e:

        return HttpResponse(str(e))

def view_item(request):

    if "lab_username" not in request.session:
        return redirect("lab_login")

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    file_name = request.GET.get("file_name")
    current_path = request.GET.get("current_path", "")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        sftp = ssh.open_sftp()

        home = f"/home/{linux_username}"

        if current_path:
            remote_file = f"{home}/{current_path}/{file_name}"
        else:
            remote_file = f"{home}/{file_name}"

        with sftp.open(remote_file, "r") as file:
            content = file.read()

            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")

        sftp.close()
        ssh.close()


        extension = ""

        if "." in file_name:
            extension = file_name.split(".")[-1].lower()

        return render(
            request,
            "virtual_lab_v2/view_file.html",
            {
                "content": content,
                "file_name": file_name,
                "current_path": current_path,
                "extension": extension,
            }
        )

    except Exception as e:

        return render(
            request,
            "virtual_lab_v2/view_file.html",
            {
                "error": str(e)
            }
        )


def save_file(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Invalid request"
        })

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    file_name = request.POST.get("file_name")
    current_path = request.POST.get("current_path")
    content = request.POST.get("content")

    home = f"/home/{linux_username}"

    if current_path:
        full_path = f"/home/{linux_username}/{current_path}/{file_name}"
    else:
        full_path = f"/home/{linux_username}/{file_name}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        sftp = ssh.open_sftp()
        print(full_path)

        with sftp.open(full_path, "w") as f:
            f.write(content)
            f.flush()

        sftp.close()
        ssh.close()

        return JsonResponse({
            "success": True
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })


def file_properties(request):

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    file_name = request.GET.get("file_name")
    current_path = request.GET.get("current_path", "")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        sftp = ssh.open_sftp()

        home = f"/home/{linux_username}"

        if current_path:
            full_path = f"{home}/{current_path}/{file_name}"
        else:
            full_path = f"{home}/{file_name}"

        info = sftp.stat(full_path)

        is_dir = stat.S_ISDIR(info.st_mode)

        permissions = stat.filemode(info.st_mode)

        modified = time.strftime(
            "%d-%b-%Y %I:%M %p",
            time.localtime(info.st_mtime)
        )

        data = {

            "success": True,

            "name": file_name,

            "type": "Folder" if is_dir else "File",

            "size": info.st_size,

            "modified": modified,

            "permissions": permissions,

            "path": full_path

        }

        sftp.close()
        ssh.close()

        return JsonResponse(data)

    except Exception as e:

        return JsonResponse({

            "success": False,

            "error": str(e)

        })
    

def copy_item(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Invalid Request"
        })

    request.session["clipboard"] = {

        "name": request.POST.get("item_name"),

        "current_path": request.POST.get("current_path", ""),

        "is_dir": request.POST.get("is_dir"),

        "action": "copy"

    }

    return JsonResponse({
        "success": True
    })


def cut_item(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Invalid Request"
        })

    request.session["clipboard"] = {

        "name": request.POST.get("item_name"),

        "current_path": request.POST.get("current_path", ""),

        "is_dir": request.POST.get("is_dir"),

        "action": "cut"

    }

    return JsonResponse({
        "success": True
    })


def paste_item(request):

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "Invalid Request"
        })

    clipboard = request.session.get("clipboard")

    if not clipboard:
        return JsonResponse({
            "success": False,
            "error": "Clipboard Empty"
        })

    linux_username = request.session["lab_username"]
    linux_password = request.session["lab_password"]

    destination_path = request.POST.get("current_path", "")

    home = f"/home/{linux_username}"

    # Source Path
    if clipboard["current_path"]:
        source = f"{home}/{clipboard['current_path']}/{clipboard['name']}"
    else:
        source = f"{home}/{clipboard['name']}"

    # Destination Path
    if destination_path:
        destination = f"{home}/{destination_path}/{clipboard['name']}"
    else:
        destination = f"{home}/{clipboard['name']}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        ssh.connect(
            hostname="10.182.4.176",
            username=linux_username,
            password=linux_password,
            look_for_keys=False,
            allow_agent=False,
        )

        # COPY
        if clipboard["action"] == "copy":

            if clipboard["is_dir"] == "true":

                command = f'cp -r "{source}" "{destination}"'

            else:

                command = f'cp "{source}" "{destination}"'

        # CUT
        else:

            command = f'mv "{source}" "{destination}"'

        stdin, stdout, stderr = ssh.exec_command(command)

        error = stderr.read().decode().strip()

        ssh.close()

        if error:

            return JsonResponse({
                "success": False,
                "error": error
            })

        # Clear clipboard after CUT
        if clipboard["action"] == "cut":
            del request.session["clipboard"]

        return JsonResponse({
            "success": True
        })

    except Exception as e:

        return JsonResponse({
            "success": False,
            "error": str(e)
        })

