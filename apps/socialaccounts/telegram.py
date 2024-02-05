import subprocess


def start_pm2_process(bot_username):
    subprocess.Popen(
        [
            "pm2",
            "start",
            f"python manage.py telebot {bot_username}",
            "--name",
            bot_username,
            "--namespace",
            "telebot",
        ]
    )


def stop_pm2_process(bot_username):
    subprocess.Popen(
        [
            "pm2",
            "stop",
            bot_username,
        ]
    )


def delete_pm2_process(bot_username):
    subprocess.Popen(
        [
            "pm2",
            "delete",
            bot_username,
        ]
    )
