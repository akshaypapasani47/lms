from .utils import (
    generate_student_credentials,
    generate_lecturer_credentials,
    send_new_account_email,
)


def post_save_account_receiver(sender, instance=None, created=False, *args, **kwargs):
    """
    For new students/lecturers with no password yet, assign ID + password and email them.

    Skip when a usable password was already set (UserCreationForm, admin, management
    commands that call set_password before save). Otherwise we would overwrite
    credentials and replace chosen usernames with auto-generated IDs.
    """
    if not created:
        return
    if getattr(instance, "_skip_auto_credentials", False):
        return
    if instance.has_usable_password():
        return

    if instance.is_student:
        username, password = generate_student_credentials()
        instance.username = username
        instance.set_password(password)
        instance.save(
            update_fields=["username", "password"]
        )  # avoid re-entering post_save for unrelated fields
        send_new_account_email(instance, password)

    elif instance.is_lecturer:
        username, password = generate_lecturer_credentials()
        instance.username = username
        instance.set_password(password)
        instance.save(update_fields=["username", "password"])
        send_new_account_email(instance, password)
