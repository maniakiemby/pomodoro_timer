import asyncio
import os
import sys
from dataclasses import dataclass
import random
import time
from datetime import datetime
import logging
from typing import Union
from decimal import Decimal
import subprocess
import signal

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
LENGTH_SESSION = 5  # 25 * 60
LENGTH_SHORT_PAUSE = 10  # 5 * 60
LENGTH_LONG_PAUSE = 25  # 30 * 60

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


def go_to_tracks():
    os.chdir(ABSOLUTE_PATH + PATH_TO_TRACKS)


def go_to_preludes():
    os.chdir(ABSOLUTE_PATH + PATH_TO_PRELUDES)


class Pomodoro:
    def __init__(self):
        self.music = None
        # self.playing = PlayMusic()

    # def start(self):
    #     self.playing.play_pomodoro()

    def change_track(self):
        # TODO zmienia odtwarzany utwór na ten pod zmienną self.music
        #  lub jeśli nic nie jest odtwarzane, zaczyna odtwarzać od początku
        pass

    def download_track_to_folder(self, link: str) -> str:
        """This method download sound from youtube.com, save to data/downloads_new/ and convert to .mp3.
        Return only title of saved track"""
        yt = YouTube(link)
        audio = yt.streams.filter(only_audio=True).first()
        if audio:
            downloaded_audio_path = audio.download(output_path=ABSOLUTE_PATH + PATH_TO_TRACKS, timeout=3, max_retries=3)
            if downloaded_audio_path:
                path = downloaded_audio_path.split('\\')[-1]
                path = self.converting_mp4_to_mp3(path)

                self.music = path
                self.change_track()

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
            try:
                os.system("""ffmpeg -i "{}" "{}""""".format(file, destination))
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

        return False


async def process_playing_in_shell(path: str = 'name of track', length: int = 'seconds', start: float = 0,
                                   volume: int = 100):
    _process = await asyncio.create_subprocess_shell(
        "ffplay -ss {start} -t {length} -volume {volume} \"{track}\" -autoexit -nodisp".format(
            track=path, length=length, start=start, volume=volume),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await _process.communicate()

    return _process
    # try:
    #     await _process
        # return True
    # except asyncio.CancelledError:
    #     return False


@dataclass
class PlayMusic:
    def __init__(self, track: str = None, tracks: list = None):
        self.track = track
        self.tracks = tracks
        self.bell = 'bell.mp3'
        self.background_music = 'copy-break-rain.mp3'
        self.start_time_playing_track: time = None
        self.stop_time_playing_track: time = None
        self.start_time_playing_pomodoro: time = None
        self.stop_time_playing_pomodoro: time = None

        self.process_playing = None

        self.which_break = 1
        self.time_already_played = 0
        self.track_time_already_played = 0
        self.part_currently_playing = None

        go_to_tracks()

    @property
    def tracks(self):
        return self.__tracks

    @tracks.setter
    def tracks(self, values):
        go_to_tracks()
        if values is None:
            self.__tracks = [x[2] for x in os.walk(os.getcwd())][0]
            random.shuffle(self.__tracks)

    # def pause_pomodoro(self):
    #     asyncio.subprocess.Process.terminate(self.process_playing)
    #     print('Pause ...')
    # os.system('pause')

    async def playing_loop(self):
        print("start pomodoro")
        while True:
            for track in self.tracks:
                while True:
                    # print('playing ...')
                    self.start_time_playing_track = time.time()
                    self.part_currently_playing = await asyncio.create_task(self.play_part_of_track(
                        track, length=int(LENGTH_SESSION - self.time_already_played),
                        start=self.track_time_already_played, volume=70))

                    # print('next playing ...')
                    # await self.part_currently_playing

                    # await asyncio.sleep(int(LENGTH_SESSION - self.time_already_played))

                    # action = input('Przerwać ? (tak/t/y)\n')
                    # os.system('pause')
                    # print("Intermission: ", intermission)  # normally return False
                    self.stop_time_playing_track = time.time()
                    self.time_already_played += self.stop_time_playing_track - self.start_time_playing_track
                    self.track_time_already_played += self.time_already_played

                    if not self.part_currently_playing:
                        print('task cancelled !!')

                        # if self.part_currently_playing:  # code 'if interrupt playing'
                        # input, który czeka na komendę
                        # albo pausa
                        # albo graj następny utwór

                        # TODO 
                        # https://stackoverflow.com/questions/30765606/whats-the-correct-way-to-clean-up-after-an-interrupted-event-loop
                        # https://github.com/scivision/asyncio-subprocess-ffmpeg/blob/main/examples/benchmark.py

                        response = await ainput("resume / next (answer)\n")
                        if response == 'resume':
                            pass
                            # self.resume_currently_playing_part_of_track()
                        elif response == 'next':
                            break
                    elif self.part_currently_playing:
                        # print('task done !!')
                        if self.time_already_played >= LENGTH_SESSION:
                            if self.which_break % 4 == 0:
                                await self.play_long_pause()
                            else:
                                await self.play_short_pause()
                            self.time_already_played = 0
                            self.start_time_playing_pomodoro = time.time()
                            self.which_break += 1
                        else:
                            break

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

    """
    def play_part_of_track(self, path: str = 'name of track', length: int = 'seconds', start: float = 0,
                           volume: int = 100):
        print('play part of track ...')
        played = True
        self.process_playing = subprocess.Popen(
            "ffplay -ss {start} -t {length} -volume {volume} \"{track}\" -autoexit -nodisp".format(
                track=path, length=length, start=start, volume=volume),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = self.process_playing.communicate()

        if self.process_playing.returncode == 0:
            played = False

        return played

    """

    async def play_part_of_track(self, path: str = 'name of track', length: int = 'seconds', start: float = 0,
                                 volume: int = 100):
        try:
            self.process_playing = await asyncio.create_task(
                process_playing_in_shell(path=path, length=length, start=start, volume=volume))
        except AttributeError:
            return False
        else:
            return True

    async def pause_currently_playing_part_of_track(self):
        await asyncio.subprocess.Process.wait(self.process_playing)

        # if self.part_currently_playing.done():
        #     return

    # TODO Dodać funkcjoonalność, która po zrobieniu pauzy w trakcie przerwy
    #  anuluje ją i będzie dalej odtwarzać utwór pomodoro

    async def play_short_pause(self):
        """Playing short break background music with bells at the beginning and at the end."""
        go_to_preludes()
        await self.play_part_of_track('bell.mp3', length=4, volume=15)
        length = LENGTH_SHORT_PAUSE - 2 * 4
        await self.play_part_of_track('copy-break-rain.mp3', length=length)
        await self.play_part_of_track('bell.mp3', length=4, volume=15)
        go_to_tracks()

    async def play_long_pause(self):
        """Playing long break background music with bells at the beginning and at the end."""
        go_to_preludes()
        await self.play_part_of_track('bell.mp3', length=4, volume=15)
        length = LENGTH_LONG_PAUSE - 2 * 4
        await self.play_part_of_track('copy-break-rain.mp3', length=length)
        await self.play_part_of_track('bell.mp3', length=4, volume=15)
        go_to_tracks()


if __name__ == '__main__':
    # print(sys.argv)
    pomodoro = Pomodoro()
    pomodoro_music = PlayMusic()
    if len(sys.argv) == 2:
        arg = sys.argv[1]

        if arg.lower() == 'play':

            async def playback_management():
                print("start playback management")
                while True:
                    response = await ainput("pause / end ?\n")
                    print(response + ' <- this is response !')

                    if response == 'pause':
                        await pomodoro_music.pause_currently_playing_part_of_track()
                    elif response == 'end':
                        pass  # todo close the application
                    else:
                        pass


            async def play_pomodoro():
                await asyncio.gather(pomodoro_music.playing_loop(), playback_management())


            asyncio.run(play_pomodoro())

            # asyncio.run(pomodoro_music.playing_loop())

        elif arg.startswith('https'):
            new_track = pomodoro.download_track_to_folder(arg)
            pomodoro_music.play_track(new_track)

        elif isinstance(arg, str):
            pomodoro_music.play_track(arg)

    if len(sys.argv) == 3 and sys.argv[1].lower() in ('convert',):
        converted_track = pomodoro.converting_mp4_to_mp3(sys.argv[2])
        print(converted_track)
