import uuid


def generate_container_name(username):

    container_name = (

        f"{username}-"

        f"{uuid.uuid4().hex[:8]}"

    )

    return container_name



def create_container():

    pass



def start_container():

    pass



def stop_container():

    pass



def restart_container():

    pass



def destroy_container():

    pass



def get_container_status():

    pass