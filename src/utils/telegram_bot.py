import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import threading
import logging
import time

class TelegramUI:
    """
    Manages the Telegram user interface for remote monitoring and control.
    Operates in a background daemon thread to prevent blocking the main execution loop.
    """
    def __init__(self, token: str, chat_id: str, risk_manager):
        if not token or not chat_id:
            logging.warning("Telegram credentials missing. Remote telemetry is disabled.")
            self.enabled = False
            return
            
        self.enabled = True
        self.chat_id = str(chat_id)
        self.bot = telebot.TeleBot(token)
        self.risk_manager = risk_manager # Dependency injection of the Risk Manager
        
        self._setup_handlers()

    def _get_keyboard(self) -> ReplyKeyboardMarkup:
        """Constructs the persistent menu for bot control."""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(KeyboardButton('🟢 Start Bot'), KeyboardButton('🛑 Stop Bot'))
        markup.row(KeyboardButton('📊 My Stats'), KeyboardButton('⚙️ Status'))
        return markup

    def _setup_handlers(self):
        """Initializes message handlers for specific commands and buttons."""
        @self.bot.message_handler(commands=['start'])
        def welcome(message):
            # Security check: only respond to the authorized chat ID
            if str(message.chat.id) == self.chat_id:
                self.bot.send_message(
                    self.chat_id, 
                    "🔮 <b>Execution Engine Online.</b>\nControl interface initialized.", 
                    parse_mode='HTML', 
                    reply_markup=self._get_keyboard()
                )
            else:
                logging.warning(f"Unauthorized access attempt from Chat ID: {message.chat.id}")

        @self.bot.message_handler(func=lambda m: str(m.chat.id) == self.chat_id)
        def handle_msg(message):
            text = message.text
            
            if text == '🛑 Stop Bot':
                self.risk_manager.set_running_status(False)
                self.send_message("<b>Brakes applied!</b> New entries are disabled 🛑")
                
            elif text == '🟢 Start Bot':
                self.risk_manager.set_running_status(True)
                self.send_message("<b>Engine started!</b> Signal monitoring resumed 🟢")
                
            elif text == '📊 My Stats':
                stats = self.risk_manager.get_statistics()
                self.send_message(stats)
                
            elif text == '⚙️ Status':
                state = self.risk_manager.state
                status = "RUNNING 🟢" if state.get('is_running', True) else "STOPPED 🛑"
                cooldown = f"⏸ <b>Cooldown:</b> until {state['paused_until']}" if state['paused_until'] else "✅ <b>Breaker:</b> Inactive"
                msg = f"🤖 <b>System Status:</b> {status}\n{cooldown}\n📦 <b>Open Positions:</b> {len(state['active_symbols'])}"
                self.send_message(msg)

    def send_message(self, msg: str):
        """Interface for external modules to push notifications to the user."""
        if not self.enabled: return
        try:
            self.bot.send_message(self.chat_id, msg, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Failed to dispatch Telegram message: {e}")

    def run(self):
        """Starts the Telegram polling loop."""
        if not self.enabled: return
        logging.info("Telegram UI polling thread initiated.")
        while True:
            try:
                self.bot.polling(none_stop=True)
            except Exception as e:
                logging.error(f"Telegram polling exception: {e}")
                time.sleep(5) # Cooldown before reconnect attempt
