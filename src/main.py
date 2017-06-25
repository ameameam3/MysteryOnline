from kivy.config import Config


Config.set('kivy', 'desktop', 1)
Config.set('input', 'mouse', 'mouse,disable_multitouch')
Config.set('kivy', 'exit_on_escape', 0)
Config.set('kivy', 'window_icon', 'icon.ico')


from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.clock import Clock

from loginscreen import LoginScreen
from mainscreen import MainScreen
from settingsscreen import SettingsScreen

from mopopup import MOPopup
from location import locations


class MainScreenManager(ScreenManager):
    main_screen = ObjectProperty(None)
    irc_connection = ObjectProperty(None)
    connected = BooleanProperty(False)

    def on_irc_connection(self, *args):
        self.irc_connection.on_join_handler = self.main_screen.on_join
        self.irc_connection.on_users_handler = self.main_screen.on_join_users
        self.irc_connection.on_disconnect_handler = self.main_screen.on_disconnect
        self.main_screen.user = App.get_running_app().get_user()
        Clock.schedule_interval(self.process_irc, 1.0/60.0)
        self.popup_ = MOPopup("Connection", "Connecting to IRC", "K", False)
        self.popup_.open()

    def on_connected(self, *args):
        self.popup_.dismiss()
        del self.popup_
        self.current = "main"
        self.main_screen.on_ready()
        Clock.schedule_interval(self.main_screen.update_chat, 1.0/60.0)

    def process_irc(self, dt):
        self.irc_connection.process()
        self.connected = self.irc_connection.is_connected()


class MysteryOnlineApp(App):
    use_kivy_settings = False

    def build(self):
        msm = MainScreenManager()
        for l in locations:
            locations[l].load()
        return msm

    def build_config(self, config):
        config.setdefaults('display', {
            'resolution': '1920x1080',
        })
        config.setdefaults('sound', {
            'blip_volume': 100
        })

    def build_settings(self, settings):
        settings.add_json_panel('Display', self.config, 'settings.json')
        settings.add_json_panel('Sound', self.config, 'settings2.json')

    def set_user(self, user):
        self.user = user

    def get_user(self):
        return self.user

    def set_main_screen(self, scr):
        self.main_screen = scr

    def get_main_screen(self):
        return self.main_screen

    def on_stop(self):
        if self.main_screen:
            self.main_screen.on_stop()
        self.config.write()
        super(MysteryOnlineApp, self).on_stop()


if __name__ == "__main__":
    MysteryOnlineApp().run()
