from kivy.app import App
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.dropdown import DropDown
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.utils import escape_markup

from character import characters
from user import User
from location import locations
from character_select import CharacterSelect

import re


class Toolbar(BoxLayout):

    def __init__(self, **kwargs):
        super(Toolbar, self).__init__(**kwargs)
        self.main_btn = None

        self.subloc_drop = DropDown(size_hint=(None, None), size=(300, 30))
        self.pos_drop = DropDown(size_hint=(None, None), size=(300, 30))
        for pos in ('center', 'right', 'left'):
            btn = Button(text=pos, size_hint=(None, None), size=(300, 30))
            btn.bind(on_release=lambda btn_: self.pos_drop.select(btn_.text))
            self.pos_drop.add_widget(btn)

        self.color_drop = DropDown(size_hint=(None, None), size=(200, 30))
        for col in ('red', 'blue', 'golden', 'green', 'FUCKING RAINBOW', 'normal'):
            btn = Button(text=col, size_hint=(None, None), size=(200, 30))
            btn.bind(on_release=lambda btn_: self.color_drop.select(btn_.text))
            self.color_drop.add_widget(btn)

        self.text_col_btn = Button(text='color', size_hint=(None, None), size=(200, 30))
        self.text_col_btn.bind(on_release=self.color_drop.open)
        self.add_widget(self.text_col_btn)
        self.color_drop.bind(on_select=self.on_col_select)

        self.pos_btn = Button(size_hint=(None, None), size=(300, 30))
        self.pos_btn.text = 'center'
        self.pos_btn.bind(on_release=self.pos_drop.open)
        self.add_widget(self.pos_btn)
        self.pos_drop.bind(on_select=self.on_pos_select)

    def update_sub(self, loc):
        for sub in loc.list_sub():
            btn = Button(text=sub, size_hint=(None, None), size=(300, 30))
            btn.bind(on_release=lambda btn_: self.subloc_drop.select(btn_.text))
            self.subloc_drop.add_widget(btn)

        self.main_btn = Button(size_hint=(None, None), size=(300, 30))
        self.main_btn.text = loc.get_first_sub()
        self.main_btn.bind(on_release=self.subloc_drop.open)
        self.add_widget(self.main_btn)
        self.subloc_drop.bind(on_select=self.on_subloc_select)

    def on_subloc_select(self, inst, subloc):
        self.main_btn.text = subloc
        main_scr = self.parent.parent  # Always blame Kivy
        main_scr.current_subloc = subloc

    def on_pos_select(self, inst, pos):
        self.pos_btn.text = pos
        main_scr = self.parent.parent  # I will never forgive Kivy
        main_scr.current_pos = pos

    def on_col_select(self, inst, col):
        self.text_col_btn.text = col
        main_scr = self.parent.parent  # I will never forgive Kivy either
        main_scr.text_box.color_change(col)


class Icon(Image):

    def __init__(self, name, ic, **kwargs):
        super(Icon, self).__init__(**kwargs)
        self.texture = ic
        self.name = name
        self.size_hint = (None, None)
        self.size = (40, 40)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.parent.parent.sprite_picked(self, self.name)
            return True


class IconsLayout(ScrollView):

    def __init__(self, **kwargs):
        super(IconsLayout, self).__init__(**kwargs)
        self.g = GridLayout(cols=6, size_hint_y=None)
        self.g.bind(minimum_height=self.g.setter('height'))
        self.add_widget(self.g)
        self.current_icon = None

    def load_icons(self, icons):
        self.g.clear_widgets()
        for i in sorted(icons.textures.keys()):
            self.g.add_widget(Icon(i, icons[i]))
        self.sprite_picked(self.g.children[-1], "1")

    def sprite_picked(self, icon, sprite_name):
        main_scr = self.parent.parent  # blame kivy
        main_scr.current_sprite = sprite_name
        if self.current_icon is not None:
            self.current_icon.color = [1, 1, 1, 1]
        icon.color = [0.3, 0.3, 0.3, 1]
        self.current_icon = icon


class SpritePreview(Image):

    center_sprite = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SpritePreview, self).__init__(**kwargs)

    def set_subloc(self, sub):
        self.texture = sub.get_img().texture

    def set_sprite(self, sprite):
        self.center_sprite.texture = sprite
        self.center_sprite.opacity = 1
        self.center_sprite.size = (self.center_sprite.texture.width / 3,
                                   self.center_sprite.texture.height / 3)


class SpriteWindow(Widget):

    background = ObjectProperty(None)
    center_sprite = ObjectProperty(None)
    left_sprite = ObjectProperty(None)
    right_sprite = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(SpriteWindow, self).__init__(**kwargs)

    def set_sprite(self, user):
        subloc = user.get_subloc()
        pos = user.get_pos()
        if pos == 'right':
            subloc.add_r_user(user)
        elif pos == 'left':
            subloc.add_l_user(user)
        else:
            subloc.add_c_user(user)

        self.display_sub(subloc)

    def set_subloc(self, subloc):
        self.background.texture = subloc.get_img().texture

    def display_sub(self, subloc):
        if subloc.c_users:
            sprite = subloc.get_c_user().get_current_sprite()
            self.center_sprite.texture = sprite
            self.center_sprite.opacity = 1
            self.center_sprite.size = self.center_sprite.texture.size
        else:
            self.center_sprite.texture = None
            self.center_sprite.opacity = 0

        if subloc.l_users:
            sprite = subloc.get_l_user().get_current_sprite()
            self.left_sprite.texture = sprite
            self.left_sprite.opacity = 1
            self.left_sprite.size = self.left_sprite.texture.size
        else:
            self.left_sprite.texture = None
            self.left_sprite.opacity = 0

        if subloc.r_users:
            sprite = subloc.get_r_user().get_current_sprite()
            self.right_sprite.texture = sprite
            self.right_sprite.opacity = 1
            self.right_sprite.size = self.right_sprite.texture.size
        else:
            self.right_sprite.texture = None
            self.right_sprite.opacity = 0


class TextBox(Label):

    char_name = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(TextBox, self).__init__(**kwargs)
        self.msg = ""
        self.prev_user = None
        self.is_displaying_msg = False
        self.markup = True
        self.colored = False
        self.selected_color = 'ffffff'
        self.raw_color = ""
        self.gen = None
        self.color_ids = ['normal', 'red', 'blue', 'golden', 'green', 'FUCKING RAINBOW']

    def display_text(self, msg, user):
        self.is_displaying_msg = True
        if self.prev_user is not user:
            self.text = ""
        self.prev_user = user
        char_name = user.get_char().name
        self.char_name.text = char_name
        self.msg = msg

        def text_gen(text):
            for c in text:
                yield c

        if self.raw_color == 'normal':
            self.gen = text_gen(self.msg)
            Clock.schedule_interval(self._animate, 1.0 / 60.0)
        else:
            self.msg = "[color={}]{}[/color]".format(self.selected_color, self.msg)
            self.text = self.msg
            self.text += " "
            self.is_displaying_msg = False

        main_scr = self.parent.parent  # BLAAAME KIVYYYY
        main_scr.log_window.add_entry(self.msg, user.username)
        main_scr.toolbar.text_col_btn.text = 'color'
        self.revert_color()

    def _animate(self, dt):
            try:
                self.text += next(self.gen)
            except StopIteration:
                self.text += " "
                self.is_displaying_msg = False
                return False

    def color_select(self, col):
        if col == 'red':
            return 'ff3333'
        elif col == 'blue':
            return '0000ff'
        elif col == 'golden':
            return 'ffd700'
        elif col == 'green':
            return '00cd00'
        elif col == 'FUCKING RAINBOW':
            return 'rainbow'
        elif col == 'normal':
            return 'ffffff'

    def color_change(self, col):
        self.raw_color = col
        self.selected_color = self.color_select(col)
        if self.selected_color != 'ffffff':
            self.colored = True
        else:
            self.colored = False

    def revert_color(self):
        self.selected_color = 'ffffff'
        self.colored = False


class LogWindow(ScrollView):

    log = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(LogWindow, self).__init__(**kwargs)

    def add_entry(self, msg, username):
        self.log.text += "{0}: [ref={2}]{1}[/ref]\n".format(username, msg, self.remove_markup(msg))
        self.scroll_y = 0

    def copy_text(self, inst, value):
        value = value.replace('&bl;', '[').replace('&br;', ']').replace('&amp', '&')
        Clipboard.copy(value)

    def remove_markup(self, msg):
        pattern = re.compile(r'\[/?color.*?\]')
        msg = re.sub(pattern, '', msg)
        return msg


class OOCWindow(TabbedPanel):

    user_list = ObjectProperty(None)
    ooc_chat = ObjectProperty(None)
    ooc_input = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(OOCWindow, self).__init__(**kwargs)
        self.online_users = {}

    def add_user(self, user):
        char = user.get_char()
        if char is None:
            char = ""
        else:
            char = char.name
        lbl = Label(text="{}: {}\n".format(user.username, char), size_hint_y=None, height=30)
        self.user_list.add_widget(lbl)
        self.online_users[user.username] = lbl

    def update_char(self, char, user):
        self.online_users[user].text = "{}: {}\n".format(user, char)

    def update_ooc(self, msg, sender):
        if sender == 'default':
            sender = App.get_running_app().get_user().username
        self.ooc_chat.text += "{0}: {1}\n".format(sender, msg)
        self.ooc_chat.parent.scroll_y = 0

    def send_ooc(self):
        Clock.schedule_once(self.refocus_text)
        msg = self.ooc_input.text
        main_scr = self.parent.parent
        irc = main_scr.manager.irc_connection
        irc.send_special('OOC', msg)
        self.ooc_input.text = ""

    def refocus_text(self, *args):
        self.ooc_input.focus = True


class RightClickMenu(ModalView):

    char_select = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(RightClickMenu, self).__init__(**kwargs)

    def on_char_select_clicked(self, *args):
        cs = CharacterSelect()
        self.dismiss()
        cs.bind(on_dismiss=self.on_picked)
        cs.open()

    def on_picked(self, inst):
        user = App.get_running_app().get_user()
        if inst.picked_char is not None:
            user.set_char(inst.picked_char)
            user.get_char().load()
            main_scr = App.get_running_app().get_main_screen()
            main_scr.on_new_char(user.get_char())


class MainScreen(Screen):

    icons_layout = ObjectProperty(None)
    sprite_preview = ObjectProperty(None)
    sprite_window = ObjectProperty(None)
    msg_input = ObjectProperty(None)
    toolbar = ObjectProperty(None)
    text_box = ObjectProperty(None)
    log_window = ObjectProperty(None)
    ooc_window = ObjectProperty(None)

    current_sprite = StringProperty("")
    current_loc = ObjectProperty(None)
    current_subloc = StringProperty("")
    current_pos = StringProperty("center")

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.user = None
        self.users = {}
        App.get_running_app().set_main_screen(self)

    def on_touch_down(self, touch):
        if touch.button == 'right':
            self.on_right_click(touch)
            return True
        super(MainScreen, self).on_touch_down(touch)

    def on_right_click(self, touch):
        menu = RightClickMenu()
        # Can't use absolute position so it uses a workaround
        menu_x = touch.pos[0] / Window.width
        menu_y = touch.pos[1] / Window.height
        if touch.pos[1] >= menu.height:
            loc_y = 'top'
        else:
            loc_y = 'y'

        menu.pos_hint = {'x': menu_x, loc_y: menu_y}
        menu.open()

    def on_ready(self, *args):
        self.msg_input.readonly = True
        self.log_window.log.bind(on_ref_press=self.log_window.copy_text)
        # Called when main screen becomes active
        self.msg_input.bind(on_text_validate=self.send_message)
        Clock.schedule_once(self.refocus_text)
        self.ooc_window.add_user(self.user)

        self.current_loc = locations['Hakuryou']
        char = self.user.get_char()
        if char is not None:
            self.on_new_char(char)

    def on_new_char(self, char):
        self.msg_input.readonly = False
        self.icons_layout.load_icons(char.get_icons())
        self.manager.irc_connection.send_special('char', char.name)

    def on_current_loc(self, *args):
        # Called when the current location changes
        self.user.set_loc(self.current_loc)
        subloc = locations['Hakuryou'].get_first_sub()
        self.current_subloc = subloc
        self.toolbar.update_sub(self.current_loc)

    def on_current_subloc(self, *args):
        # Called when the current sublocation changes
        subloc = self.current_loc.get_sub(self.current_subloc)
        self.user.set_subloc(subloc)
        self.sprite_preview.set_subloc(subloc)

    def on_current_pos(self, *args):
        pass

    def on_current_sprite(self, *args):
        # Called when user picks new sprite
        self.user.set_current_sprite(self.current_sprite)
        sprite = self.user.get_current_sprite()
        self.sprite_preview.set_sprite(sprite)
        Clock.schedule_once(self.refocus_text, 0.1)

    def send_message(self, *args):
        self.user.set_pos(self.current_pos)
        Clock.schedule_once(self.refocus_text)
        msg = escape_markup(self.msg_input.text)
        col_id = 0
        if self.text_box.colored:
            col_id = self.text_box.color_ids.index(self.text_box.raw_color)
        self.msg_input.text = ""
        user = self.user
        loc = user.get_loc().name
        char = user.get_char().name
        self.manager.irc_connection.send_msg(msg, loc, self.current_subloc, char,
                                             self.current_sprite, self.current_pos, col_id)

    def refocus_text(self, *args):
        # Refocusing the text input has to be done this way cause Kivy
        self.msg_input.focus = True

    def update_chat(self, dt):
        if self.text_box.is_displaying_msg:
            return
        msg = self.manager.irc_connection.get_msg()
        if msg is not None:
            if msg.identify() == 'chat':
                dcd = msg.decode()
                if dcd[0] == "default":
                    user = self.user
                else:
                    user = self.users[dcd[0]]
                    user.set_from_msg(*dcd)
                self.sprite_window.set_subloc(user.get_subloc())
                self.sprite_window.set_sprite(user)
                col = self.text_box.color_ids[int(dcd[6])]
                self.text_box.color_change(col)
                self.text_box.display_text(dcd[7], user)

            elif msg.identify() == 'char':
                dcd = msg.decode_other()
                self.update_char(*dcd)
            elif msg.identify() == 'OOC':
                dcd = msg.decode_other()
                self.ooc_window.update_ooc(*dcd)

    def update_char(self, char, user):
        self.ooc_window.update_char(char, user)
        if char not in characters:
            self.users[user].set_char(characters['RedHerring'])
            self.users[user].set_current_sprite('4')
        else:
            self.users[user].set_char(characters[char])
        self.users[user].get_char().load()

    def on_join(self, username):
        if username not in self.users:
            self.users[username] = User(username)
            self.ooc_window.add_user(self.users[username])
        self.log_window.log.text += "{} has joined.\n".format(username)
        self.log_window.log.scroll_y = 0
        char = self.user.get_char()
        if char is not None:
            self.manager.irc_connection.send_special('char', char.name)

    def on_disconnect(self, username):
        self.log_window.log.text += "{} has disconnected.\n".format(username)
        self.log_window.log.scroll_y = 0

    def on_join_users(self, users):
        users = users.split()
        for u in users:
            if u == "@"+self.user.username:
                continue
            if u != self.user.username:
                self.users[u] = User(u)
                self.ooc_window.add_user(self.users[u])
