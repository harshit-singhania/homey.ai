"""Telegram Bot API service client"""
import logging
from typing import Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.constants import ParseMode

from app.models.message import OutgoingMessage, InlineKeyboardButton as InlineKeyboardButtonModel

logger = logging.getLogger(__name__)


class TelegramBotClient:
    """
    Telegram Bot API client for sending messages, photos, and interactive messages.
    Handles rate limiting (30 msg/sec per user, 20 msg/min to groups) automatically
    via python-telegram-bot library.
    """

    def __init__(self, token: str):
        """
        Initialize Telegram Bot client.

        Args:
            token: Telegram Bot API token from @BotFather
        """
        self.bot = Bot(token=token)
        logger.info("TelegramBotClient initialized")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: Optional[str] = None
    ) -> int:
        """
        Send a text message to a Telegram user.

        Args:
            chat_id: Telegram chat ID (user's telegram_id)
            text: Message text to send
            parse_mode: Optional parse mode ('HTML' or 'Markdown')

        Returns:
            message_id of the sent message

        Raises:
            TelegramError: If message sending fails
        """
        try:
            parse_mode_enum = None
            if parse_mode == "HTML":
                parse_mode_enum = ParseMode.HTML
            elif parse_mode == "Markdown":
                parse_mode_enum = ParseMode.MARKDOWN

            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode_enum
            )
            logger.info(f"Sent message to {chat_id}: message_id={message.message_id}")
            return message.message_id

        except TelegramError as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            raise

    async def send_photo(
        self,
        chat_id: int,
        photo: str,  # file_id or URL
        caption: Optional[str] = None,
        parse_mode: Optional[str] = None
    ) -> int:
        """
        Send a photo to a Telegram user.

        Args:
            chat_id: Telegram chat ID
            photo: Either Telegram file_id (to reuse) or URL to upload
            caption: Optional caption text
            parse_mode: Optional parse mode for caption

        Returns:
            message_id of the sent message

        Raises:
            TelegramError: If photo sending fails
        """
        try:
            parse_mode_enum = None
            if parse_mode == "HTML":
                parse_mode_enum = ParseMode.HTML
            elif parse_mode == "Markdown":
                parse_mode_enum = ParseMode.MARKDOWN

            message = await self.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                parse_mode=parse_mode_enum
            )
            logger.info(f"Sent photo to {chat_id}: message_id={message.message_id}")
            return message.message_id

        except TelegramError as e:
            logger.error(f"Failed to send photo to {chat_id}: {e}")
            raise

    async def send_interactive(
        self,
        chat_id: int,
        text: str,
        inline_keyboard: list[list[InlineKeyboardButtonModel]],
        parse_mode: Optional[str] = None
    ) -> int:
        """
        Send a message with inline keyboard buttons.

        Args:
            chat_id: Telegram chat ID
            text: Message text
            inline_keyboard: 2D array of InlineKeyboardButton models
            parse_mode: Optional parse mode

        Returns:
            message_id of the sent message

        Raises:
            TelegramError: If message sending fails
        """
        try:
            # Convert Pydantic models to telegram.InlineKeyboardButton objects
            telegram_keyboard = []
            for row in inline_keyboard:
                telegram_row = []
                for button in row:
                    telegram_button = InlineKeyboardButton(
                        text=button.text,
                        callback_data=button.callback_data
                    )
                    telegram_row.append(telegram_button)
                telegram_keyboard.append(telegram_row)

            reply_markup = InlineKeyboardMarkup(telegram_keyboard)

            parse_mode_enum = None
            if parse_mode == "HTML":
                parse_mode_enum = ParseMode.HTML
            elif parse_mode == "Markdown":
                parse_mode_enum = ParseMode.MARKDOWN

            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode_enum
            )
            logger.info(f"Sent interactive message to {chat_id}: message_id={message.message_id}")
            return message.message_id

        except TelegramError as e:
            logger.error(f"Failed to send interactive message to {chat_id}: {e}")
            raise

    async def send(self, chat_id: int, message: OutgoingMessage) -> bool:
        """
        Send a message based on OutgoingMessage schema.

        Args:
            chat_id: Telegram chat ID
            message: OutgoingMessage Pydantic model

        Returns:
            True if message sent successfully

        Raises:
            ValueError: If message type is invalid or required fields are missing
            TelegramError: If Telegram API call fails
        """
        try:
            if message.type == "text":
                if not message.text:
                    raise ValueError("text field is required for type='text'")
                await self.send_message(
                    chat_id=chat_id,
                    text=message.text,
                    parse_mode=message.parse_mode
                )

            elif message.type == "photo":
                photo = message.photo_file_id or message.photo_url
                if not photo:
                    raise ValueError("photo_file_id or photo_url required for type='photo'")
                await self.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=message.text,
                    parse_mode=message.parse_mode
                )

            elif message.type == "interactive":
                if not message.text or not message.inline_keyboard:
                    raise ValueError("text and inline_keyboard required for type='interactive'")
                await self.send_interactive(
                    chat_id=chat_id,
                    text=message.text,
                    inline_keyboard=message.inline_keyboard,
                    parse_mode=message.parse_mode
                )

            else:
                raise ValueError(f"Unknown message type: {message.type}")

            return True

        except (ValueError, TelegramError) as e:
            logger.error(f"Failed to send message: {e}")
            raise

    async def get_me(self):
        """
        Get information about the bot.

        Returns:
            Bot user object
        """
        return await self.bot.get_me()
