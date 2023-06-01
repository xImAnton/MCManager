from __future__ import annotations

import pathlib
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..server import Server


class LaunchMethod:
    METHOD: str = "null"

    @classmethod
    def could_satisfy(cls, path: pathlib.Path) -> Optional[str]:
        pass

    def __init__(self, path: pathlib.Path, args: str):
        self.path: pathlib.Path = path
        self.args: str = args

    def to_tuple(self) -> tuple[str, str]:
        return self.METHOD, self.args

    def is_valid(self):
        pass

    def get_command(self, java: str, ram: str):
        pass


class LaunchMethodManager:
    _METHODS: list[type[LaunchMethod]] = []

    @classmethod
    def register(cls, mng: type[LaunchMethod]):
        cls._METHODS.append(mng)

    @classmethod
    def get_method(cls, srv: Server) -> Optional[LaunchMethod]:
        method = srv.launch_method

        for mng in cls._METHODS:
            if mng.METHOD == method[0]:
                return mng(srv.path, method[1])

        return None

    @classmethod
    def find_matching_method(cls, srv: Server) -> Optional[LaunchMethod]:
        for mng in cls._METHODS:
            if args := mng.could_satisfy(srv.path):
                return mng(srv.path, args)

        return None
