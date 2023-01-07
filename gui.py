import os
import subprocess
# from subprocess import Popen, CREATE_NEW_CONSOLE
import asyncio
import sys
from asyncio import new_event_loop, get_event_loop
import threading

import kivy
from kivy.config import Config
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.atlas import Atlas
from aioconsole import ainput

from main import PlayMusic, Pomodoro


kivy.require('2.1.0')
__version__ = '0.1'

RUNNING_PATH = os.getcwd()
Config.set('graphics', 'width', '700')
Config.set('graphics', 'height', '250')
Config.write()


# class Play(threading.Thread):
#     def run(self) -> None:
#         play = PlayMusic()
#         asyncio.run(play.playing_loop())
#         play.stop_pomodoro()


class Player(FloatLayout):
    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)
        self.stage = 'no play'
        # preperation, play, pause
        self.playing = self.ids['playing']
        self.playing.bind(on_release=self.play_pomodoro)
        self.playing_image = self.ids['playing_image']  # names: play, no play
        self.next = self.ids['next']
        self.timer = self.ids['timer']
        self.volume = self.ids['volume']
        self.volume_image = self.ids['volume_image']
        # names: full-volume, default=voice, low-volume, no-audio (bez podkładu, sam dzwonek), mute
        self.break_or_work = self.ids['break_or_work']
        self.new_item = self.ids['new_item']
        self.ids['download'].bind(on_release=self.download_new_track)
        self.ids['settings'].bind(on_release=self.open_settings)

        self.play_music = PlayMusic()
        self.thread_play_music = None

    def play_pomodoro(self, *args):
        if self.stage == 'no play':
            self.play()

        elif self.stage == 'play':
            self.stop()

        # elif self.stage == 'pause':
        #     self.resume()

    def play(self, *args):
        self.playing_image.source = "atlas://data//images//myatlas/resume"
        self.stage = 'play'

        self.thread_play_music = threading.Thread(target=self.play_music.playing_loop)
        self.thread_play_music.start()

        # self.thread_play_music.join()

    def stop(self, *args):
        self.playing_image.source = "atlas://data//images//myatlas/play"
        self.stage = 'no play'

        self.play_music.playing = False
        self.play_music.part_currently_playing.stop()
        self.play_music.reset()

    # def resume(self, *args):
    #     self.playing_image.source = "atlas://data//images//myatlas/resume"
    #     self.stage = 'play'

    def download_new_track(self, *args):
        pass

    def open_settings(self, *args):
        # open file with settings
        pass


class MyApp(App):
    def build(self):
        Window.clearcolor = (151/255, 152/255, 164/255)
        return Player()


if __name__ == '__main__':
    app = MyApp()
    app.run()

    try:
        sys.exit(app.stop())
    except SystemExit:
        print('Player Window Closed')
