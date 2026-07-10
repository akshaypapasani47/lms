from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import VirtualLab
import paramiko
import subprocess
import re
paramiko.util.log_to_file("ssh_debug.log")
import warnings
warnings.filterwarnings("ignore")
# Create your views here.


def clean_output(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def virtual_lab_list(request):
    labs = VirtualLab.objects.all()
    # labs = [
    #     {"id": 1, "name": "Python Lab"},
    #     {"id": 2, "name": "Linux Lab"},
    # ]
    return render(request, 'virtual_lab/index.html', {"labs": labs})


# def lab_detail(request, id):
#     return render(request, 'virtual_lab/lab_detail.html', {"id": id})



client = None
channel = None

def lab_detail(request, id):
    global client, channel
    lab = get_object_or_404(VirtualLab, id=id)
    output = ""

    if request.method == "POST":
        command = request.POST.get("command")

        try:

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 🔐 USE KEY AUTH (NOT PASSWORD)
            key = paramiko.Ed25519Key.from_private_key_file(
                r"C:\Users\pakshaykumar\.ssh\id_ed25519"
            )

            client.connect(
                hostname='10.180.16.12',
                port=44124,
                username='Akshay',   # ⚠️ make sure this is correct for lab
                pkey=key,
                look_for_keys=False,
                allow_agent=False,
                auth_timeout=60,
                banner_timeout=60
            )

            # ✅ FIX: use client (not ssh)
            stdin, stdout, stderr = client.exec_command(command)

            output = stdout.read().decode() + stderr.read().decode()
            channel = client.invoke_shell()

            channel.send(command + "\n")

            import time
            time.sleep(1)  # wait for response

            output = ""

            while channel.recv_ready():
                output += channel.recv(4096).decode()

            output = clean_output(output)

            client.close()

        except Exception as e:
            output = str(e)

    return render(
        request,
        'virtual_lab/lab_detail.html',
        {
            "lab": lab,
            "output": output
        }
    )



# def lab_detail(request, id):

#     #lab = VirtualLab.objects.get(id=id)
#     lab = get_object_or_404(VirtualLab, id=id)
#     output = ""
#     if request.method == "POST":
#         command = request.POST.get("command")
#         try:
            
#             client = paramiko.SSHClient()
#             client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

#             client.connect(
#                 hostname='10.180.16.12',
#                 port=44124,
#                 username='Akshay',
#                 password='AK47@cdac',
#                 look_for_keys=False,
#                 auth_timeout=60,
#                 banner_timeout=60,
#                 # auth_handler=handler
#                 # hostname=lab.remote_ip,
#                 # port=int(lab.port),
#                 # username=lab.username,
#                 # password=lab.password
#             )
            
#             stdin, stdout, stderr = ssh.exec_command(command)

#             output = stdout.read().decode()+ stderr.read().decode()


#             client.close()

#         except Exception as e:
#             output = str(e)

#     return render(
#         request,
#         'virtual_lab/lab_detail.html',
#         {
#             "lab": lab,
#             "output": output
#         }
#     )

# # def virtual_lab_list(request):
# #     return render(request, 'virtual_lab/index.html')


# # def ssh_test(request):

# #     ssh = paramiko.SSHClient()
# #     ssh.load_system_host_keys()
# #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# #     ssh.connect(
# #         hostname='127.0.0.1',
# #         username='pakshaykumar',
# #         password='Akki@ak47',
# #         allow_agent=False,
# #         look_for_keys=False,
# #         auth_timeout=30,
# #         banner_timeout=30
        
# #     )

# #     stdin, stdout, stderr = ssh.exec_command('command')

# #     output = stdout.read().decode()

# #     ssh.close()

# #     return HttpResponse(output)



