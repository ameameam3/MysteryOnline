from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.utils import escape_markup

from irc_mo import PrivateConversation


class PrivateMessageScreen(ModalView):
    pm_body = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(PrivateMessageScreen, self).__init__(**kwargs)
        self.conversations = []
        self.irc = None
        self.username = ''
        self.current_conversation = None
        self.conversation_list = getattr(self.ids, 'prv_users_list')
        self.text_box = getattr(self.ids, 'pm_input')
        self.pm_close_sound = SoundLoader.load('sounds/general/codecover.wav')
        self.pm_window_open_flag = False
        self.pm_flag = False

    def ready(self):
        main_scr = App.get_running_app().get_main_screen()
        self.pm_body.bind(on_ref_press=main_scr.log_window.copy_text)

    def set_current_conversation(self, conversation):
        self.current_conversation = conversation

    def open_conversation(self, conversation):
        self.set_current_conversation(conversation)
        self.update_pms()

    def get_conversation_for_user(self, username):
        if len(self.conversations) is 0:
            self.build_conversation(username)
            return self.get_conversation_for_user(username)
        else:
            for c in self.conversations:
                if c.username == username:
                    return c

    def set_current_conversation_user(self, username):
        conversation = self.get_conversation_for_user(username)
        self.current_conversation = conversation

    def prv_chat_close_btn(self):
        vol = App.get_running_app().config.getdefaultint('sound', 'effect_volume', 100)
        self.pm_close_sound.volume = vol / 100
        self.pm_close_sound.play()
        self.pm_window_open_flag = False
        self.pm_flag = False
        self.dismiss()

    def build_conversation(self, username):
        is_init = False
        if username is not self.username:
            for c in self.conversations:
                if username == c.username:
                    is_init = True
            if not is_init:
                self.add_conversation(username)

    def add_conversation(self, username):
        conversation = PrivateConversation()
        conversation.username = username
        self.conversations.append(conversation)
        btn = Button(text=username, size_hint_y=None, height=50, width=self.conversation_list.width)
        btn.bind(on_press=lambda x: self.open_conversation(conversation))
        self.conversation_list.add_widget(btn)
        self.current_conversation = conversation

    def update_conversation(self, sender, msg):
        if 'www.' in msg or 'http://' in msg or 'https://' in msg:
            msg = "[u]{}[/u]".format(msg)
        self.current_conversation.msgs += "{0}: [ref={2}]{1}[/ref]\n".format(sender, msg, escape_markup(msg))
        self.update_pms()

    def update_pms(self):
        self.pm_body.text = self.current_conversation.msgs
        self.pm_body.parent.scroll_y = 0

    def refocus_text(self, *args):
        self.text_box.focus = True

    def send_pm(self):
        sender = self.username
        if self.current_conversation is not None:
            if self.text_box.text != "":
                    receiver = self.current_conversation.username
                    self.irc.send_private_msg(receiver, sender, self.text_box.text)
                    msg = self.text_box.text
                    if 'www.' in msg or 'http://' in msg or 'https://' in msg:
                        msg = "[u]{}[/u]".format(msg)
                    self.current_conversation.msgs += "{0}: [ref={2}]{1}[/ref]\n".format(sender, msg,
                                                                                         escape_markup(msg))
                    self.pm_body.text = self.current_conversation.msgs
                    self.text_box.text = ''
                    self.pm_body.parent.scroll_y = 0
                    Clock.schedule_once(self.refocus_text, 0.1)