import sys
import traceback

from django.core.management.base import BaseCommand, CommandError
from telebot import TeleBot, formatting

from messagecore.models import Message
from socialaccounts.models import ProxySocialApp
from users.models import User, UserRole


class Command(BaseCommand):
    help = "Run telegram bot service"

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
                bot = ProxySocialApp.objects.get(client_id=bot_username)
            except ProxySocialApp.DoesNotExist:
                raise CommandError(f"{bot_username} does not exist!")

            telebot = TeleBot(bot.secret)
            if not bool(bot.secret):
                raise CommandError("Empty secret key!")

            @telebot.message_handler(commands=["status", "stop", "restart"])
            def send_commands(message):
                admin_user = self.get_admin_user(message.chat.id)

                if admin_user:
                    message_text = message.text.split(" ")
                    content = message_text[0].lstrip("/")
                    title = " ".join(message_text[1:])

                    if bool(title):
                        Message.objects.create(
                            telegram_bot_username=bot.client_id,
                            telegram_chat_id=0,
                            title=title,
                            content=content,
                            origin=admin_user.email,
                            type=Message.COMMAND,
                        )
                        telebot.send_message(
                            message.chat.id,
                            formatting.format_text(
                                formatting.mcode(f"{content} {title}"),
                                r"Request successful\!",
                                separator=" ",
                            ),
                            parse_mode="MarkdownV2",
                        )
                    else:
                        telebot.send_message(
                            message.chat.id,
                            formatting.format_text(
                                formatting.mcode(f"{content} {title}"),
                                "Request failed: missing args",
                                separator=" ",
                            ),
                            parse_mode="MarkdownV2",
                        )
                else:
                    telebot.send_message(
                        message.chat.id,
                        "You do not have permission to perform this action.",
                    )

            telebot.infinity_polling()

        except KeyboardInterrupt:
            self.stdout.write("Shutdown requested. Process terminated.")
            sys.exit(0)

        except Exception:
            traceback.print_exc(file=sys.stdout)
            sys.exit(1)

    def get_admin_user(self, telegram_chat_id):
        try:
            user = User.objects.get(telegram_chat_id=telegram_chat_id)
            user = user if user.role.name == UserRole.ADMIN else None
            return user
        except User.DoesNotExist:
            raise CommandError(
                f"Admin user with telegram_chat_id={telegram_chat_id} does not exist!"
            )
        except User.MultipleObjectsReturned:
            raise CommandError("This telegram_chat_id is linked to multiple users!")
