from .docker_service import (

    create_container,

    start_container,

    stop_container,

    restart_container,

    destroy_container,

    get_container_status,

)


def start_workspace():

    return{

        "workspace_status":"RUNNING",

        "container_status":"RUNNING",

        "message":"Workspace Started Successfully"

    }

def stop_workspace():

    return{

        "workspace_status":"STOPPED",

        "container_status":"STOPPED",

        "message":"Workspace Stopped Successfully"

    }

def restart_workspace():

    return{

        "workspace_status":"RUNNING",

        "container_status":"RUNNING",

        "message":"Workspace Restarted Successfully"

    }



def destroy_workspace():

    return {

        "status":"DESTROYED",

        "message":"Workspace Destroyed Successfully"

    }



def get_workspace_status():

    pass