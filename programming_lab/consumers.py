import json
import threading

import docker

from channels.generic.websocket import WebsocketConsumer


class ProgrammingTerminalConsumer(WebsocketConsumer):

    def connect(self):

        self.accept()

        self.user = self.scope["user"]

        if not self.user.is_authenticated:

            self.send(text_data=json.dumps({
                "output": "User is not authenticated.\r\n"
            }))

            self.close()

            return


        try:

            from .models import StudentContainer


            student_container = StudentContainer.objects.filter(
                user=self.user
            ).first()


            if not student_container:

                self.send(text_data=json.dumps({
                    "output":
                    "No Docker programming lab found.\r\n"
                }))

                self.close()

                return


            self.container_id = (
                student_container.container_id
            )


            self.client = docker.from_env()


            self.container = (
                self.client.containers.get(
                    self.container_id
                )
            )


            # Check Docker container status

            if self.container.status != "running":

                self.send(text_data=json.dumps({
                    "output":
                    "Docker container is not running.\r\n"
                }))

                self.close()

                return


            # Create interactive bash session

            self.exec_instance = (
                self.container.exec_run(
                    cmd="/bin/bash",
                    tty=True,
                    stdin=True,
                    socket=True
                )
            )


            self.socket = self.exec_instance.output


            self.send(text_data=json.dumps({
                "output":
                "\r\n"
                "================================\r\n"
                " Docker Programming Lab\r\n"
                "================================\r\n"
                "Connected successfully.\r\n"
                "Container: "
                f"{self.container.name}\r\n"
                "\r\n"
            }))


            # Start thread to continuously read Docker output

            self.output_thread = threading.Thread(

                target=self.read_output,

                daemon=True

            )

            self.output_thread.start()


        except Exception as error:

            print(
                "DOCKER TERMINAL ERROR:",
                error
            )


            try:

                self.send(text_data=json.dumps({
                    "output":
                    f"\r\nDocker error: {error}\r\n"
                }))

            except Exception:

                pass


            self.close()


    def receive(self, text_data):

        try:

            data = json.loads(text_data)


            if "input" not in data:

                return


            user_input = data["input"]


            if not user_input:

                return


            self.socket.send(
                user_input.encode()
            )


        except Exception as error:

            print(
                "TERMINAL INPUT ERROR:",
                error
            )


    def read_output(self):

        while True:

            try:

                output = self.socket.recv(
                    4096
                )


                if not output:

                    break


                output = output.decode(
                    errors="ignore"
                )


                self.send(
                    text_data=json.dumps({
                        "output": output
                    })
                )


            except Exception as error:

                print(
                    "TERMINAL OUTPUT ERROR:",
                    error
                )

                break


    def disconnect(self, close_code):

        print(
            "PROGRAMMING TERMINAL DISCONNECTED:",
            close_code
        )


        try:

            if hasattr(self, "socket"):

                self.socket.close()

        except Exception:

            pass


        try:

            if hasattr(self, "client"):

                self.client.close()

        except Exception:

            pass