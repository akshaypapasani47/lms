import paramiko
import time
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse


def clean_output(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# GLOBAL SSH SESSION
client = None
channel = None

# TERMINAL LOGIN PAGE
def terminal_login(request):

    if request.method == "POST":

        username = request.POST.get("username")

        #password = request.POST.get("password")

        try:

            # TEST SSH LOGIN
            test_client = paramiko.SSHClient()

            test_client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )
            key = paramiko.Ed25519Key.from_private_key_file(r"C:\Users\pakshaykumar\.ssh\id_ed25519")
            test_client.connect(
                hostname='10.180.16.12',
                port=44124,
                username=username,
                pkey=key,
                look_for_keys=False,
                allow_agent=False
            )

            test_client.close()

            # SAVE SESSION
            request.session['terminal_username'] = username

            #request.session['terminal_password'] = password

            return redirect('/terminal/')

        except Exception as e:

            return render(
                request,
                'interactive_terminal/login.html',
                {
                    'error': 'Invalid terminal credentials'
                }
            )

    return render(
        request,
        'interactive_terminal/login.html'
    )


# TERMINAL PAGE
def terminal_home(request):

    global client, channel

    # CHECK LOGIN
    if 'terminal_username' not in request.session:

        return redirect('/terminal/login/')

    username = request.session['terminal_username']

    try:

        # CONNECT ONLY ONCE
        if client is None:

            client = paramiko.SSHClient()

            client.set_missing_host_key_policy(
                paramiko.AutoAddPolicy()
            )

            key = paramiko.Ed25519Key.from_private_key_file(
                r"C:\Users\pakshaykumar\.ssh\id_ed25519"
            )

            client.connect(
                hostname='10.180.16.12',
                port=44124,
                username=username,
                pkey=key,
                look_for_keys=False,
                allow_agent=False
            )

            # REAL TERMINAL SHELL
            channel = client.invoke_shell()

            time.sleep(1)

        return render(
            request,
            'interactive_terminal/terminal.html'
        )

    except Exception as e:

        print("TERMINAL ERROR:", e)

        return redirect('/terminal/login/')


# def terminal_home(request):

#     global client, channel

#     # CHECK TERMINAL LOGIN
#     if not request.session.get('terminal_logged_in'):

#         return redirect('/terminal/login/')

#     username = request.session['terminal_username']

#     if client is None:

#         client = paramiko.SSHClient()

#         client.set_missing_host_key_policy(
#             paramiko.AutoAddPolicy()
#         )

#         key = paramiko.Ed25519Key.from_private_key_file(
#             r"C:\Users\pakshaykumar\.ssh\id_ed25519"
#         )

#         client.connect(
#             hostname='10.180.16.12',
#             port=44124,
#             username=username,
#             pkey=key,
#             look_for_keys=False,
#             allow_agent=False
#         )

#         transport = client.get_transport()

#         channel = transport.open_session()

#         channel.get_pty()

#         channel.invoke_shell()

#         time.sleep(1)

#     return render(
#         request,
#         'interactive_terminal/terminal.html'
#     )
# def terminal_home(request):

#     global client, channel

#     # CHECK LOGIN
#     if 'terminal_username' not in request.session:

#         return redirect('/terminal/login/')

#     username = request.session['terminal_username']

#     #password = request.session['terminal_password']

#     # CONNECT ONLY ONCE
#     if client is None:

#         client = paramiko.SSHClient()

#         client.set_missing_host_key_policy(
#             paramiko.AutoAddPolicy()
#         )
#         key = paramiko.Ed25519Key.from_private_key_file(
#             r"C:\Users\pakshaykumar\.ssh\id_ed25519"
#         )
#         client.connect(
#             hostname='10.180.16.12',
#             port=44124,
#             username=username,
#             pkey=key,
#             look_for_keys=False,
#             allow_agent=False
#         )

#         # START TERMINAL
#         transport = client.get_transport()

#         channel = transport.open_session()

#         channel.get_pty()

#         channel.invoke_shell()

#         time.sleep(1)

#     return render(
#         request,
#         'interactive_terminal/terminal.html'
#     )


# RUN COMMANDS
def run_command(request):

    global channel

    # CHECK LOGIN
    if 'terminal_username' not in request.session:

        return JsonResponse({
            "output": "Not logged in"
        })

    output = ""

    if request.method == "POST":

        command = request.POST.get("command")

        if command:

            channel.send(command + "\n")

            time.sleep(1)

            while channel.recv_ready():

                output += channel.recv(4096).decode()

            output = clean_output(output)

    return JsonResponse({
        "output": output
    })

def terminal_logout(request):

    global client, channel

    # CLEAR SESSION
    request.session.flush()

    # CLOSE SSH
    if channel:
        channel.close()

    if client:
        client.close()

    channel = None
    client = None

    return redirect('/terminal/login/')

# def terminal_home(request):

#     global client, channel

#     # CONNECT ONLY ONCE
#     if client is None:

#         client = paramiko.SSHClient()

#         client.set_missing_host_key_policy(
#             paramiko.AutoAddPolicy()
#         )

#         # LOAD SSH KEY
#         key = paramiko.Ed25519Key.from_private_key_file(
#             r"C:\Users\pakshaykumar\.ssh\id_ed25519"
#         )

#         client.connect(
#             hostname='10.180.16.12',
#             port=44124,
#             username='Akshay',
#             pkey=key,
#             look_for_keys=False,
#             allow_agent=False
#         )

#         # 🔥 START REAL TERMINAL
#         #channel = client.invoke_shell()
#         transport = client.get_transport()
#         channel = transport.open_session()
#         #channel = client.invoke_shell(term='xterm')
#         channel.get_pty()
#         channel.invoke_shell()
#         time.sleep(1)

#     return render(
#         request,
#         'interactive_terminal/terminal.html'
#     )


# def run_command(request):

#     global channel

#     output = ""

#     if request.method == "POST":

#         command = request.POST.get("command")

#         if command:

#             # SEND COMMAND
#             channel.send(command + "\n")

#             time.sleep(1)

#             # RECEIVE OUTPUT
#             while channel.recv_ready():

#                 output += channel.recv(4096).decode()
#             output = clean_output(output)

#     return JsonResponse({
#         "output": output
#     })

