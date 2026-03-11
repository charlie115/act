import aiohttp
import asyncio
import sys
import time
import traceback
import threading

from django.core.management.base import BaseCommand, CommandError

from messagecore.models import Message
from socialaccounts.models import ProxySocialApp


TELEGRAM_BOT_SENDMESSAGE_URL = "https://api.telegram.org/bot{token}/sendMessage"


class Command(BaseCommand):
    help = "Telegram bot sends message-core messages to users telegram chats"

    def add_arguments(self, parser):
        parser.add_argument(
            "username",
            type=str,
            help="Telegram bot username (or client_id)",
        )

    def handle(self, *args, **kwargs):
        try:
            bot_username = kwargs["username"]

            try:
                self.bot = ProxySocialApp.objects.get(client_id=bot_username)
            except ProxySocialApp.DoesNotExist:
                raise CommandError(f"{bot_username} does not exist!")

            while True:
                messages = Message.objects.filter(
                    telegram_bot_username=bot_username,
                    sent=False,
                )

                for message in messages:
                    self.stdout.write(
                        f"Message {message.id} | {message.title} | {message.telegram_chat_id}"
                    )

                    thread = threading.Thread(
                        target=self.process_message,
                        args=(message,),
                        daemon=True,
                    )
                    thread.start()

                    message.sent = True
                    message.save()

                time.sleep(1)

        except KeyboardInterrupt:
            self.stdout.write("Shutdown requested. Process terminated.")
            sys.exit(0)

        except Exception:
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

    def process_message(self, message):
        sent_times = message.send_times

        while sent_times > 0:
            asyncio.run(
                self.send_message(
                    msg_id=message.id,
                    chat_id=message.telegram_chat_id,
                    text=message.content,
                )
            )
            sent_times -= 1
            time.sleep(message.send_term)

    async def send_message(self, msg_id, chat_id, text):
        url = TELEGRAM_BOT_SENDMESSAGE_URL.format(token=self.bot.secret)
        params = {
            "chat_id": chat_id,
            "text": text,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, params=params) as response:
                if response.status == 200:
                    self.stdout.write(
                        self.style.SUCCESS(f"Message #{msg_id} successfully sent!")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Message #{msg_id} not sent: {response}")
                    )
