import asyncio
import os
import sys
import threading
from dataclasses import dataclass
import random
import time
from time import perf_counter
from datetime import datetime
import logging
from typing import Union
from decimal import Decimal
import subprocess
import signal

import psutil
from aioconsole import ainput
import ffmpeg
from pytube import YouTube

# from pydub import AudioSegment
# from pydub.playback import play, _play_with_simpleaudio

"""This program will accompany you at work, helping you focus on tasks.
 I use the pomodoro method here."""

"""W sesji, czyli po włączeniu programu losują się utwory jakie będą grane (główny podkład, krótki przerywnik
 i długi przerywnik). W bazie jest kilka podstawowych utworów kilka podkładów - tylko podkłady będzie można dodać.
 Będzie przycisk do zmiany podkładu na inny. Po dodaniu nowego utworu od razu będzie on grany i zamieniany z obecnego
 na nowy."""

# AudioSegment.ffmpeg = "C:\\ffmpeg\\bin\\ffmpeg.exe"

# all lengths in seconds
LENGTH_SESSION = 25 * 60
LENGTH_SHORT_PAUSE = 5 * 60
LENGTH_LONG_PAUSE = 30 * 60
COUNT_SESSIONS = 3  # po ilu sesjach jest dłuższa przerwa

# paths
ABSOLUTE_PATH = os.getcwd()
PATH_TO_TRACKS = '\data\downloads_new'
PATH_TO_PRELUDES = '\data'

if not ABSOLUTE_PATH.endswith('Pomodoro'):
    location_split = ABSOLUTE_PATH.split("\\")
    while len(location_split) > 0 and location_split[-1] != 'Pomodoro':
        location_split.pop()
        if len(location_split) == 0:
            raise PermissionError(
                "Unrecognized localization. probably the application was not launched from the right place "
                "or the folder arrangement is wrong."
            )
    ABSOLUTE_PATH = '\\'.join(location_split)


def track_in_location(track: str) -> Union[bool, Exception]:
    if os.path.exists(track):
        return True
    else:
        raise FileNotFoundError("track {} not found in current location. Current location: {}".format(
            track, os.getcwd()))


def go_to_tracks():
    os.chdir(ABSOLUTE_PATH + PATH_TO_TRACKS)


def go_to_preludes():
    os.chdir(ABSOLUTE_PATH + PATH_TO_PRELUDES)


def file_in_location(file_name: str) -> bool:
    if os.path.exists(file_name):
        return True
    else:
        return False


class Pomodoro:
    def __init__(self):
        self.music = None
        self.link_to_download = None
        # self.playing = PlayMusic()

    # def start(self):
    #     self.playing.play_pomodoro()

    def change_track(self):
        # TODO zmienia odtwarzany utwór na ten pod zmienną self.music
        #  lub jeśli nic nie jest odtwarzane, zaczyna odtwarzać od początku
        pass

    def download_track_to_folder(self, link: str = None) -> str:
        """This method download sound from youtube.com, save to data/downloads_new/ and convert to .mp3.
        Return only title of saved track"""
        if link:
            yt = YouTube(link)
        else:
            yt = YouTube(self.link_to_download)

        # print('length: {}'.format(yt.length))
        name_of_track = yt.title + 'mp3'
        if file_in_location(name_of_track):
            return ' fasle'  # todo sprawdzić czemu to jest takie dziwne
            # raise FileExistsError('File already exists.')

        audio = yt.streams.filter(only_audio=True).first()
        # print('filesize_approx: {}'.format(audio.filesize_approx))
        if audio:
            downloaded_audio = audio.download(output_path=ABSOLUTE_PATH + PATH_TO_TRACKS,
                                              skip_existing=True, timeout=3, max_retries=3)
            if downloaded_audio:
                path = downloaded_audio.split('\\')[-1]
                path = self.converting_mp4_to_mp3(path)

                # self.music = path
                # self.change_track()

                return path
            else:
                raise ConnectionError(
                    "There is probably a problem with your internet connection."
                )
        else:
            raise SystemError(
                "There may have been a problem finding the audio track."
                "Variable 'audio' is {} but could be YouTube object.".format(type(audio))
            )

    @staticmethod
    def converting_mp4_to_mp3(file: str) -> Union[str, bool]:
        os.chdir(ABSOLUTE_PATH + PATH_TO_TRACKS)
        if os.path.exists(file):
            base, ext = os.path.splitext(file)
            destination = base + '.mp3'
            if os.path.exists(destination):
                return False
            try:
                os.system("ffmpeg -i \"{}\" \"{}\"".format(file, destination))
            except TypeError:
                print("Problem with converting file using ffmpeg.")
            else:
                if os.path.exists(destination):
                    # todo nie usuwa starego pliku !
                    #  chociaż po chwili usunęło, hmm..

                    os.remove(file)
                os.chdir(ABSOLUTE_PATH)
                return destination
        else:
            raise FileNotFoundError(
                "In current path '{}' don't exists.\ncurrent location: {}".format(file, os.getcwd()))

        # return False


def shell_playing(path, length, starting_moment=0, volume=100):
    with subprocess.Popen("ffplay -ss {start} -t {length} -volume {volume} \"{track}\" -autoexit -nodisp".format(
            track=path, length=length, start=starting_moment, volume=volume),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) as proc:
        return


class ThreadPlayingMusic(threading.Thread):
    def __init__(self, path, length, starting_moment=0, volume=70):
        super(ThreadPlayingMusic, self).__init__()
        self.daemon = True
        self._stop_event = threading.Event()

        self.path = path
        self.length = length
        self.starting_moment = starting_moment
        self.volume = volume
        self.process_playing = None

    def run(self) -> None:
        with subprocess.Popen("ffplay -ss {start} -t {length} -volume {volume} \"{track}\" -autoexit -nodisp".format(
                track=self.path, length=self.length, start=self.starting_moment, volume=self.volume),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) as self.process_playing:
            return

    def stop(self) -> None:
        parent = psutil.Process(self.process_playing.pid)
        for child in parent.children(recursive=True):
            child.terminate()
        parent.terminate()

        self._stop_event.set()  # czy to jest potrzebne ?

    def stopped(self) -> int:  # sprawdzić, czy napewno zwraca inta
        return self._stop_event.is_set()


@dataclass
class PlayMusic:
    def __init__(self, track: str = None, tracks: list = None):
        self.track = track
        self.tracks = tracks
        self.bell = 'bell.mp3'
        self.background_music = 'copy-break-rain.mp3'
        self.start_time_playing_track: time = None
        self.stop_time_playing_track: time = None

        self.is_playing = False
        self.is_break = False

        self.which_break = 1
        self.pomodoro_session_time_already_played = 0
        self.track_time_already_played = 0
        self.part_currently_playing = None

        go_to_tracks()

    def reset(self):
        self.start_time_playing_track: time = None
        self.stop_time_playing_track: time = None

        self.is_playing = False
        self.is_break = False

        self.which_break = 1
        self.pomodoro_session_time_already_played = 0
        self.track_time_already_played = 0
        self.part_currently_playing = None

    @property
    def tracks(self):
        return self.__tracks

    @tracks.setter
    def tracks(self, values):
        go_to_tracks()
        if values is None:
            self.__tracks = [x[2] for x in os.walk(os.getcwd())][0]
            random.shuffle(self.__tracks)

    def playing_loop(self):
        while self.is_playing:
            for track in self.tracks:
                while self.is_playing:
                    self.start_time_playing_track = time.time()
                    length = int(LENGTH_SESSION - self.pomodoro_session_time_already_played)

                    self.part_currently_playing = ThreadPlayingMusic(
                        path=track, length=length, starting_moment=self.track_time_already_played)
                    self.part_currently_playing.start()
                    self.part_currently_playing.join()

                    self.stop_time_playing_track = time.time()
                    self.pomodoro_session_time_already_played += \
                        self.stop_time_playing_track - self.start_time_playing_track
                    self.track_time_already_played += self.pomodoro_session_time_already_played

                    if self.part_currently_playing.stopped():
                        if self.is_playing:
                            break
                        else:
                            self.reset()
                            return

                    if self.pomodoro_session_time_already_played >= LENGTH_SESSION:
                        self.is_break = True
                        if self.which_break % COUNT_SESSIONS == 0:
                            self.play_long_pause()
                        else:
                            self.play_short_pause()
                        self.pomodoro_session_time_already_played = 0
                        self.which_break += 1
                        self.is_break = False
                self.track_time_already_played = 0

    @staticmethod
    def play_track(path: str = 'name of track', volume: int = 100):
        if not os.path.exists(path):
            os.chdir(ABSOLUTE_PATH)
        elif not os.path.exists(path):
            go_to_preludes()
        elif not os.path.exists(path):
            go_to_tracks()
        else:
            subprocess.run("ffplay -volume {volume} \"{track}\" -autoexit -nodisp".format(
                volume=volume, track=path))

    def stop_pomodoro(self):
        self.part_currently_playing.stop()

    def play_short_pause(self):
        """Playing short break background music with bells at the beginning and at the end."""
        go_to_preludes()
        if self.is_playing:
            self.part_currently_playing = ThreadPlayingMusic(path='bell.mp3', length=4, volume=15)
            self.part_currently_playing.start()
            self.part_currently_playing.join()
        length = LENGTH_SHORT_PAUSE - 2 * 4
        if self.is_playing:
            self.part_currently_playing = ThreadPlayingMusic(path='copy-break-rain.mp3', length=length)
            self.part_currently_playing.start()
            self.part_currently_playing.join()
        if self.is_playing:
            self.part_currently_playing = ThreadPlayingMusic(path='bell.mp3', length=4, volume=15)
            self.part_currently_playing.start()
            self.part_currently_playing.join()
        go_to_tracks()

    def play_long_pause(self):
        """Playing long break background music with bells at the beginning and at the end."""
        go_to_preludes()
        if self.is_playing:
            self.part_currently_playing = ThreadPlayingMusic(path='bell.mp3', length=4, volume=15)
            self.part_currently_playing.start()
            self.part_currently_playing.join()
        length = LENGTH_LONG_PAUSE - 2 * 4
        if self.is_playing:
            self.part_currently_playing = ThreadPlayingMusic(path='copy-break-rain.mp3', length=length)
            self.part_currently_playing.start()
            self.part_currently_playing.join()
        if self.is_playing:
            self.part_currently_playing = ThreadPlayingMusic(path='bell.mp3', length=4, volume=15)
            self.part_currently_playing.start()
            self.part_currently_playing.join()
        go_to_tracks()


if __name__ == '__main__':
    # print(sys.argv)
    pomodoro = Pomodoro()
    pomodoro_music = PlayMusic()
    if len(sys.argv) == 2:
        arg = sys.argv[1]

        if arg.lower() == 'play':

            pomodoro_music.playing_loop()

        elif arg.startswith('https'):
            new_track = pomodoro.download_track_to_folder(arg)
            pomodoro_music.play_track(new_track)

        elif isinstance(arg, str):
            pomodoro_music.play_track(arg)

    if len(sys.argv) == 3 and sys.argv[1].lower() in ('convert',):
        converted_track = pomodoro.converting_mp4_to_mp3(sys.argv[2])
        print(converted_track)
