

from channels.generic.websocket import WebsocketConsumer
import paramiko
import json
import time
import threading
from .models import ActiveSession
from django.utils import timezone

class TerminalConsumer(WebsocketConsumer):

    def connect(self):
        self.last_activity = time.time()
        self.accept()
        
        self.username = self.scope["session"].get("lab_username")
        self.password = self.scope["session"].get("lab_password")

        ActiveSession.objects.create(
            username=self.username,
            login_time=timezone.now(),
            active=True,
            last_activity=timezone.now()
        )

        if not self.username or not self.password:
            self.close()
            return

        self.client = paramiko.SSHClient()

        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy()
        )
        try:

            self.client.connect(
                hostname="10.182.4.176",
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False
            )

            transport = self.client.get_transport()
            transport.set_keepalive(30)

            self.ssh_channel = self.client.invoke_shell(term='xterm')
            self.ssh_channel.send("bash --login\n")
            # self.ssh_channel.send(
            #     'export PS1="\\u@\\h:\\w\\$ "\n'
            # )
            
            self.ssh_channel.settimeout(0)

            threading.Thread(
                target=self.read_output,
                daemon=True
            ).start()

            threading.Thread(
                target=self.check_timeout,
                daemon=True
            ).start()

        except Exception as e:
            print("SSH ERROR:", e)
            self.close()
            return

        # time.sleep(1)

        # if self.ssh_channel.recv_ready():

        #     output = self.ssh_channel.recv(
        #         4096
        #     ).decode(errors="ignore")

        #     self.send(
        #         text_data=json.dumps({
        #             "output": output
        #         })
        #     )

    

    def receive(self, text_data):

        self.last_activity = time.time()

        try:

            data = json.loads(text_data)

            print("PARSED =", data)

            #
            # NEW PART
            #
            if (
                isinstance(data, dict)
                and "current_path" in data
            ):

                current_path = data["current_path"]

                if current_path:

                    self.ssh_channel.send(
                        f"cd /home/{self.username}/{current_path}\n"
                    )

                else:

                    self.ssh_channel.send(
                        f"cd /home/{self.username}\n"
                    )

                return

            #
            # EXISTING RESIZE CODE
            #
            if (
                isinstance(data, dict)
                and "resize" in data
            ):

                self.ssh_channel.resize_pty(

                    width=data["resize"]["cols"],

                    height=data["resize"]["rows"]

                )

                return

        except json.JSONDecodeError:

            pass

        ActiveSession.objects.filter(

            username=self.username,

            active=True

        ).update(

            last_activity=timezone.now()

        )

        self.ssh_channel.send(text_data)


                    

        # print("COMMAND =", text_data)

        # self.ssh_channel.send(text_data)

        # time.sleep(1)

        # output = ""

        # while self.ssh_channel.recv_ready():

        #     output += self.ssh_channel.recv(
        #         4096
        #     ).decode()

        # self.send(
        #     text_data=json.dumps({
        #         "output": output
        #     })
        # )

    def read_output(self):

        while True:

            try:

                if self.ssh_channel.recv_ready():

                    output = self.ssh_channel.recv(
                        4096
                    ).decode(errors="ignore")

                    self.send(
                        text_data=json.dumps({
                            "output": output
                        })
                    )

            except Exception:
                break




    def check_timeout(self):
        while True:
            time.sleep(60)
            if time.time() - self.last_activity > 300:
                print(
                    f"TIMEOUT: {self.username}"
                )
                self.close()
                break
    



    def disconnect(self, close_code):
        
        
        # if hasattr(self, "ssh_channel"):
        #     self.ssh_channel.close()

        # if hasattr(self, "client"):
        #     self.client.close()

        print("DISCONNECT CALLED")

        session = ActiveSession.objects.filter(
            username=self.username,
            active=True
        ).order_by("-login_time").first()

        if session:
            session.active = False
            session.logout_time = timezone.now()
            session.save()
        

        try:

            self.ssh_channel.close()

            self.client.close()

        except:

            pass


    