import subprocess


def start_pm2_process(bot_username, process_name):
    process = subprocess.Popen(
        [
            "pm2",
            "start",
            f"python manage.py {process_name} {bot_username}",
            "--name",
            f"{bot_username}.{process_name}",
            "--namespace",
            bot_username,
        ]
    )
    process.wait()


def stop_pm2_process(bot_username, process_name=None):
    process_to_stop = bot_username
    if process_name:
        process_to_stop += f".{process_name}"

    process = subprocess.Popen(
        [
            "pm2",
            "stop",
            process_to_stop,
        ]
    )
    process.wait()


def delete_pm2_process(bot_username, process_name=None):
    process_to_delete = bot_username
    if process_name:
        process_to_delete += f".{process_name}"

    process = subprocess.Popen(
        [
            "pm2",
            "delete",
            process_to_delete,
        ]
    )
    process.wait()
