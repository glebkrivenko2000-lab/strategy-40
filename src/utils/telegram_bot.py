import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import logging
from typing import Callable

class TelegramUI:
    """
    Класс для управления интерфейсом Telegram.
    Запускается в фоновом потоке (daemon thread).
    """
    def __init__(self, token: str, chat_id: str, risk_manager):
        if not token or not chat_id:
            logging.warning("Telegram credentials not provided. Notifications disabled.")
            self.enabled = False
            return
            
        self.enabled = True
        self.chat_id = str(chat_id)
        self.bot = telebot.TeleBot(token)
        self.risk_manager = risk_manager # Ссылка на RiskManager для получения статуса
        
        self._setup_handlers()

    def _get_keyboard(self) -> ReplyKeyboardMarkup:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(KeyboardButton('🟢 Start Bot'), KeyboardButton('🛑 Stop Bot'))
        markup.row(KeyboardButton('📊 My Stats'), KeyboardButton('⚙️ Status'))
        return markup

    def _setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def welcome(message):
            if str(message.chat.id) == self.chat_id:
                self.bot.send_message(
                    self.chat_id, 
                    "🔮 <b>Execution Engine Online.</b>\nUse buttons below.", 
                    parse_mode='HTML', 
                    reply_markup=self._get_keyboard()
                )
            else:
                logging.warning(f"Unauthorized TG access attempt from ID: {message.chat.id}")

        @self.bot.message_handler(func=lambda m: str(m.chat.id) == self.chat_id)
        def handle_msg(message):
            text = message.text
            
            if text == '🛑 Stop Bot':
                self.risk_manager.set_running_status(False)
                self.send_message("<b>Brakes applied!</b> New entries are disabled 🛑")
                
            elif text == '🟢 Start Bot':
                self.risk_manager.set_running_status(True)
                self.send_message("<b>Engine started!</b> Searching for signals 🟢")
                
            elif text == '📊 My Stats':
                stats = self.risk_manager.get_statistics()
                self.send_message(stats)
                
            elif text == '⚙️ Status':
                state = self.risk_manager.state
                status = "RUNNING 🟢" if state.get('is_running', True) else "STOPPED 🛑"
                pause = f"⏸ <b>Pause until:</b> {state['paused_until']}" if state['paused_until'] else "✅ <b>Breaker:</b> Inactive"
                msg = f"🤖 <b>System Status:</b> {status}\n{pause}\n📦 <b>Positions:</b> {len(state['active_symbols'])}"
                self.send_message(msg)

    def send_message(self, msg: str):
        """Публичный метод для отправки уведомлений из других модулей."""
        if not self.enabled: return
        try:
            self.bot.send_message(self.chat_id, msg, parse_mode='HTML')
        except Exception as e:
            logging.error(f"TG Send Error: {e}")

    def run(self):
        """Запуск поллинга в текущем потоке."""
        if not self.enabled: return
        logging.info("Telegram UI thread started.")
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                logging.error(f"TG Polling Error: {e}")
                time.sleep(5)
