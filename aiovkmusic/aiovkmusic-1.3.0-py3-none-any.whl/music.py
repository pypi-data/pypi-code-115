import asyncio
import os
from pathlib import PurePath

from ffmpeg import FFmpeg

from .exceptions import PlaylistsAccessDenied, NonExistentUser, InvalidBitrate, TracksAccessDenied
from .model import Track, Playlist
from .session import VKSession
from vk_api import exceptions as vk_api_exceptions

SEARCH_MISS_NUMBER = 5


class Music:
    def __init__(self, user: str, session: VKSession):
        """
        Создание интерфейса доступа к музыке вконтакте с пользователем по умолчанию.
        :param user: id пользователя или ссылка на его профиль.
        :param session: Объект сессии с авторизованным пользователем.
        """
        self._api = session.api
        self._audio = session.audio
        _user = self.screen_name(user)
        object_info = self._api.method(
            'utils.resolveScreenName', {'screen_name': _user}
        )
        if not object_info:
            raise NonExistentUser(user)
        self._user_id = object_info['object_id']
        self._user_info = self._api.method("users.get", {"user_ids": self._user_id})

    def playlists(self, owner_id: int | None = None) -> [Playlist]:
        """
        Возвращает плейлисты указанного пользователя.
        Если не указывать owner_id, то по умолчанию
        используется id заданного в экземпляре класса пользователя (self.user_id).
        :param owner_id: id пользователя чьи плейлисты нужно найти.
        :return: Список найденных плейлистов.
        """
        _owner_id = owner_id if owner_id else self.user_id
        try:
            albums = self._audio.get_albums(owner_id=_owner_id)
        except vk_api_exceptions.AccessDenied:
            raise PlaylistsAccessDenied(_owner_id)
        return [
            Playlist(
                id=album['id'],
                owner_id=album['owner_id'],
                url=album['url'],
                plays=album['plays'],
                title=album['title'],
                access_hash=album['access_hash']
            )
            for album in albums
        ]

    def user_tracks(self, user_id: int | None = None, count: int = 5, offset: int = 0) -> [Track]:
        """
        Возвращает сохранённые аудиозаписи указанного пользователя.
        Если не указывать user_id, то по умолчанию
        используется id заданного в экземпляре класса пользователя (self.user_id).
        :param user_id: id пользователя чьи сохранённые аудиозаписи нужно вернуть.
        :param count: Количество аудиозаписей, которые нужно вернуть.
        :param offset: Смещение по сохранённым аудиозаписям пользователя.
        :return: Список найденных аудиозаписей с учётом смещения.
        """
        _owner_id = user_id if user_id else self.user_id
        i = -1
        tracks = []
        try:
            for track in self._audio.get_iter(owner_id=_owner_id):
                i += 1
                if i == count + offset:
                    break
                elif i < offset:
                    continue
                else:
                    tracks.append(
                        Track(
                            id=track['id'],
                            owner_id=track['owner_id'],
                            duration=track['duration'],
                            url=track['url'],
                            _covers=track['track_covers'],
                            artist=track['artist'],
                            title=track['title']
                        )
                    )
        except vk_api_exceptions.AccessDenied:
            raise TracksAccessDenied(_owner_id)

        return tracks

    def search(self, text: str, count: int = 5, offset: int = 0, official=False) -> [Track]:
        """
        Поиск музыки по названию.
        Приблизительно время скачивания:
            1 аудиозапись - от ~3 сек,
            5 аудиозапись - от ~7 сек,
            10 аудиозапись - от ~11 сек,
            15 аудиозапись - от ~15 сек.
        :param text: Название песни, или её автор, или что-либо другое (Аналогично поиску в ВК).
        :param count: Количество аудиозаписей которые должен вернуть поиск.
        :param offset: Смещение от начала списка найденных аудиозаписей.
        :param official: Возвращает только музыку от исполнителей (не от обычных пользователей).
        *Так как применяется фильтрация по автору, то количество найденных аудиозаписей может
        быть меньше заданного значения count.
        :return: Список найденных аудиозаписей с учётом смещения.
        """
        search_generator = self._audio.search_iter(q=text, offset=offset)
        i = 0
        miss = 0
        tracks = []
        while i < count:
            track = next(search_generator)
            if official:
                if track['owner_id'] < 0:
                    miss = 0
                else:
                    if miss > SEARCH_MISS_NUMBER:
                        break
                    miss += 1
                    continue
            i += 1
            tracks.append(Track(
                id=track['id'],
                owner_id=track['owner_id'],
                duration=track['duration'],
                url=track['url'],
                _covers=track['track_covers'],
                artist=track['artist'],
                title=track['title']
            ))
        return tracks

    def track(self, owner_id: int, track_id: int) -> Track:
        """
        Аудиозапись.
        :param owner_id: id владельца аудиозаписи.
        :param track_id: id аудиозаписи.
        :return: Аудиозапись.
        """
        track = self._audio.get_audio_by_id(owner_id=owner_id, audio_id=track_id)
        return Track(
            id=track['id'],
            owner_id=track['owner_id'],
            duration=track['duration'],
            url=track['url'],
            _covers=track['track_covers'],
            artist=track['artist'],
            title=track['title']
        )

    def playlist_tracks(self, playlist: Playlist) -> [Track]:
        """
        Возвращает список аудиозаписей заданного плейлиста.
        :param playlist: Плейлист чьи аудиозаписи нужно вернуть.
        :return: Список аудиозаписей плейлиста.
        """
        tracks = self._audio.get(
            album_id=playlist.id,
            owner_id=playlist.owner_id,
            access_hash=playlist.access_hash
        )
        return [
            Track(
                id=track['id'],
                owner_id=track['owner_id'],
                duration=track['duration'],
                url=track['url'],
                _covers=track['track_covers'],
                artist=track['artist'],
                title=track['title']
            )
            for track in tracks
        ]

    async def download(
            self,
            *tracks: Track,
            path: str = './',
            bitrate: int = 320
    ) -> [Track]:
        """
        Загружает аудиозаписи.
        :param tracks: Аудиозаписи для скачивания.
        :param path: Путь по которому будут сохранены аудиозаписи.
        :param bitrate: Битрейт.
        :return: Список аудиозаписей с установленным path.
        """
        self._mkdir(path)
        to_download = []
        _tracks = tracks[0] if len(tracks) == 1 and isinstance(tracks[0], list | tuple) else tracks
        for track in _tracks:
            track.path = str(PurePath(path, track.fullname + '.mp3'))
            to_download.append(self._downloader(track.url, track.path, bitrate=bitrate))
        await asyncio.gather(*to_download)
        return _tracks

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def first_name(self) -> str:
        return self._user_info[0]['first_name']

    @property
    def last_name(self) -> str:
        return self._user_info[0]['last_name']

    @staticmethod
    def screen_name(text: str) -> str:
        if '/' in text:
            text = text.replace('/', ' ').strip().split()[-1]
        if text.isdigit():
            text = 'id' + text
        return text

    @staticmethod
    async def _downloader(url: str, name: str, bitrate: int):
        if bitrate not in (320, 192, 256, 128, 160, 6, 32):
            raise InvalidBitrate(bitrate)
        await FFmpeg().option('y').option(
            'http_persistent', 'false'
        ).input(url).output(
            name, {'b:a': f'{bitrate}k'}
        ).execute()

    @staticmethod
    def _mkdir(dirname: str):
        if dirname not in ('./', '.', ''):
            os.makedirs(PurePath(dirname), exist_ok=True)
