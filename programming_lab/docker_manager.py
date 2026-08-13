import docker
import re
import os

from django.conf import settings

from docker.errors import NotFound, APIError


def get_client():
    return docker.from_env()


# def create_container(username):

#     client = get_client()

#     safe_username = re.sub(
#         r"[^a-zA-Z0-9_.-]",
#         "_",
#         username
#     )

#     container_name = f"{safe_username}_lab"

#     container = client.containers.run(
#         image="programming-lab:latest",
#         name=container_name,
#         tty=True,
#         stdin_open=True,
#         detach=True
#     )

#     return {
#         "id": container.id,
#         "name": container.name
#     }


def create_container(username):

    client = get_client()

    safe_username = re.sub(
        r'[^a-zA-Z0-9_.-]',
        '_',
        username
    )

    container_name = f"{safe_username}_lab"

    # Django's physical directory for this student's files
    host_workspace = os.path.join(
        settings.MEDIA_ROOT,
        "programming_lab",
        safe_username
    )

    # Make sure the directory exists
    os.makedirs(
        host_workspace,
        exist_ok=True
    )

    try:

        container = client.containers.get(
            container_name
        )

        if container.status != "running":
            container.start()

        return {
            "id": container.id,
            "name": container.name
        }

    except NotFound:

        container = client.containers.run(

            image="programming-lab:latest",

            name=container_name,

            tty=True,

            stdin_open=True,

            detach=True,

            volumes={
                host_workspace: {
                    "bind": "/workspace",
                    "mode": "rw"
                }
            },

            working_dir="/workspace"

        )

        return {
            "id": container.id,
            "name": container.name
        }





def get_container(container_id):

    client = get_client()

    try:

        return client.containers.get(container_id)

    except NotFound:

        return None


def get_container_status(container_id):

    container = get_container(container_id)

    if container is None:

        return "NOT_FOUND"

    container.reload()

    if container.status == "running":

        return "RUNNING"

    return "STOPPED"


def start_container(container_id):

    container = get_container(container_id)

    if container is None:

        return False

    try:

        container.start()

        return True

    except Exception:

        return False


def stop_container(container_id):

    container = get_container(container_id)

    if container is None:

        return False

    try:

        container.stop()

        return True

    except Exception:

        return False


def restart_container(container_id):

    container = get_container(container_id)

    if container is None:

        return False

    try:

        container.restart()

        return True

    except Exception:

        return False


def delete_container(container_id):

    container = get_container(container_id)

    if container is None:

        return False

    try:

        container.remove(force=True)

        return True

    except Exception:

        return False









# import docker
# import re
# from docker.errors import NotFound, APIError

# def get_client():
#     return docker.from_env()

# def test_connection():

#     client = get_client()

#     return client.ping()


# def create_container(username):

#     client = get_client()

#     safe_username = re.sub(
#         r'[^a-zA-Z0-9_.-]',
#         '_',
#         username
#     )

#     container_name = f"{safe_username}_lab"

#     try:
#         container = client.containers.get(container_name)

#         if container.status != "running":
#             container.start()

#         return {
#             "id": container.id,
#             "name": container.name
#         }

#     except NotFound:

#         container = client.containers.run(
#             image="programming-lab:latest",
#             name=container_name,
#             tty=True,
#             detach=True
#         )

#         return {
#             "id": container.id,
#             "name": container.name
#         }

# def stop_container(container_id):

#     client = get_client()

#     container = client.containers.get(container_id)

#     try:
#         container.stop()
#     except:
#         pass

# def start_container(container_id):

#     client = get_client()

#     container = client.containers.get(container_id)

#     try:
#         container.start()
#     except:
#         pass

# def delete_container(container_id):

#     client = get_client()

#     container = client.containers.get(container_id)

#     try:
#         container.remove(force=True)
#     except:
#         pass