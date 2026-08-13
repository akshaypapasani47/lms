from django.contrib.auth.models import User



def is_lab_admin(request):

    user = request.user

    return (

        user.is_superuser

        or

        getattr(

            user,

            "role",

            None

        )=="lecturer"

    )




def is_student(request):

    user=request.user

    return (

        getattr(

            user,

            "role",

            None

        )=="student"

    )




def can_access_workspace(request):

    return (

        is_student(request)

        or

        is_lab_admin(request)

    )




def can_create_lab(request):

    return (

        is_lab_admin(request)

    )




def can_access_terminal(request):

    return (

        can_access_workspace(request)

    )




def can_access_file_manager(request):

    return (

        can_access_workspace(request)

    )




def can_access_assignments(request):

    return (

        can_access_workspace(request)

    )