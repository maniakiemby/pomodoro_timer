import datetime
import os
import subprocess
# from subprocess import Popen, CREATE_NEW_CONSOLE
import asyncio
import sys
import time
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
from kivy.clock import Clock

from main import PlayMusic, Pomodoro


kivy.require('2.1.0')
__version__ = '0.1'

RUNNING_PATH = os.getcwd()
Config.set('graphics', 'width', '800')
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
        self.next.bind(on_release=self.next_track)
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

        self.play_music.is_playing = True
        self.thread_play_music = threading.Thread(target=self.play_music.playing_loop)
        self.thread_play_music.start()

        self.timer.beginning()

        self.break_or_work.text = 'Czas sesji, teraz skup się na zadaniu.'
        self.break_or_work.font_size = '34sp'
        # self.break_or_work.pos_hint = {'x': .25}

        # self.thread_play_music.join()

    def stop(self, *args):
        self.playing_image.source = "atlas://data//images//myatlas/play"
        self.stage = 'no play'

        self.play_music.is_playing = False
        self.play_music.part_currently_playing.stop()
        # self.play_music.reset()

        self.timer.time_start = None

        self.break_or_work.text = 'Czas przerwy, teraz jest czas na rozluźnienie umysłu.'
        self.break_or_work.font_size = '20sp'
        # self.break_or_work.pos_hint = {'x': .45}

    # def resume(self, *args):
    #     self.playing_image.source = "atlas://data//images//myatlas/resume"
    #     self.stage = 'play'

    def next_track(self, *args):
        if not self.play_music.is_break and self.play_music.is_playing:
            self.play_music.part_currently_playing.stop()
        # todo dodać komunikat, że nie można zmieniać utworu w trakcie przerwy.

    def download_new_track(self, *args):
        pass

    def open_settings(self, *args):
        # open file with settings
        pass


class Timer(Label):
    def __init__(self, **kwargs):
        super(Timer, self).__init__(**kwargs)
        self.time_str = '%H:%M:%S'
        self.text = time.strftime(self.time_str)
        Clock.schedule_interval(self.update_time, 1)
        self.time_start = None

    def update_time(self, stopwatch_time=False, *args):
        if self.time_start:
            t = time.time()
            diff_time = t - self.time_start
            self.text = time.strftime(self.time_str, time.gmtime(diff_time))
        else:
            self.text = time.strftime(self.time_str)

    # def to_count(self):
    #     self.text

    def beginning(self):
        # super(Timer, self).__init__(text=time.strftime('00:00'))
        # self.text = time.strftime('00:00')
        # Clock.schedule_interval(self.update_time, 1)
        self.time_start = time.time()


class MyApp(App):

    def build(self):
        Window.clearcolor = (151/255, 152/255, 164/255)
        return Player()

    # def on_stop(self):
    #     print('Goodbye')
    #     _app = App.get_running_app()
    #     print(App.get_running_app().__str__())
    #     print(App.get_running_app()._app_name())
    #     print(dir(App.get_running_app()))
    #     if _app.play_music.is_playing:
    #         _app.stop()
        # print(_app.walk())
        # if _app.play_music.is_playing:
        #     _app.play_music.stop()


if __name__ == '__main__':
    app = MyApp()
    print(app.__str__())
    app.run()

    try:
        sys.exit(app.stop())
    except SystemExit:
        print('Player Window Closed')
