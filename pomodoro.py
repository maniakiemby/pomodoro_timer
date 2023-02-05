# coding=UTF-8
import datetime
import os
import subprocess
# from subprocess import Popen, CREATE_NEW_CONSOLE
# import asyncio
import sys
import time
# from asyncio import new_event_loop, get_event_loop
import threading

import kivy
import psutil
from kivy.config import Config
# from kivy.clock import mainthread
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.atlas import Atlas
# from aioconsole import ainput
from kivy.clock import Clock

from main import PlayMusic, Pomodoro, ABSOLUTE_PATH


kivy.require('2.1.0')
__version__ = '0.1'

RUNNING_PATH = os.getcwd()
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '250')
Config.write()


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
            self.start_playing()

        elif self.stage == 'play':
            self.stop_playing()

        # elif self.stage == 'pause':
        #     self.resume()

    def start_playing(self, *args):
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

    def stop_playing(self, *args):
        self.playing_image.source = "atlas://data//images//myatlas/play"
        self.stage = 'no play'

        self.play_music.is_playing = False
        if self.play_music.part_currently_playing:
            self.play_music.part_currently_playing.stop()

        self.timer.time_start = None

        self.break_or_work.text = 'Naciśnij play aby zacząć sesję pomodoro.'
        self.break_or_work.font_size = '20sp'
        # self.break_or_work.pos_hint = {'x': .45}

    # def resume(self, *args):
    #     self.playing_image.source = "atlas://data//images//myatlas/resume"
    #     self.stage = 'play'

    def next_track(self, *args):
        if not self.play_music.is_break and self.play_music.is_playing:
            try:
                self.play_music.stop_pomodoro()
            except psutil.NoSuchProcess("Song cannot be changed, no such actually playing process."):
                raise

        # todo dodać komunikat, że nie można zmieniać utworu w trakcie przerwy.

    def wrapped_download(self):
        # todo: zmienić ikonę pobierania na jakiś 'oczekiwacz'
        #  i zablokować możliwość rozpoczęcia kolejnego procesu pobierania.

        pomodoro = Pomodoro()
        pomodoro.link_to_download = self.new_item.text
        pomodoro.download_track_to_folder()
        self.play_music.tracks = None  # This triggers the addition of a new track to the mixtape
        print('Downloading and converting are done.')

        # todo: zmienić spowrotem na ikonę pobierania i odblokować jego działanie

        return True
        # todo: Dodać coś, żeby wątek się skończył, obecne zachowanie wygląda jakby się nie kończył.

    def download_new_track(self, *args):
        download_mp3 = threading.Thread(target=self.wrapped_download)
        download_mp3.start()

        # TODO: dodać w tym miejscu blokadę na przycisk download do momentu wykonania w całości zadania.
        #  może być tak, że plik już istnieje dodać jakąś metodę, która by o tym informowała
        #  i nie pobierała nie potrzebnie drugi raz tego pliu.

        #  todo dodatkowe: dodać jakieś ładowanie / informację na temat tego ile czasu jeszcze zajmie
        #   pobieranie i convertowanie pliku.

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

    def beginning(self):
        self.time_start = time.time()


class ButtonDownload(Button):
    def __init__(self, **kwargs):
        super(ButtonDownload, self).__init__(**kwargs)
        self.blockade = False

    def lock(self):
        self.blockade = True

    def unlock(self):
        self.blockade = False


class PomodoroApp(App):
    def build(self):
        Window.clearcolor = (151/255, 152/255, 164/255)
        return Player()

    def on_stop(self):
        App.get_running_app().root.stop_playing()

        # todo: nie działa to wyłączanie


if __name__ == '__main__':
    app = PomodoroApp()
    # print(app.__str__())
    app.run()

    # try:
    #     sys.exit(app.stop())
    # except SystemExit:
    #     print('Player Window Closed')
