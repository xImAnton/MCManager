import pathlib


class ServerProperties:
    def __init__(self, path: pathlib.Path):
        self.path: pathlib.Path = path
        self._data: dict[str, str] = {}
        self._changed_keys: set[str] = set()

        with self.path.open("r") as f:
            data = f.readlines()

        for i, line in enumerate(data):
            line = line.strip()

            if line.startswith("#"):
                continue

            if "=" not in line:
                continue

            eq_index = line.find("=")
            self._data[line[:eq_index]] = line[eq_index+1:]

    def get_value(self, key: str) -> str:
        return self._data[key]

    def set_value(self, key: str, value, save: bool = False):
        self._changed_keys.add(key)
        self._data[key] = str(value)

        if save:
            self.save()

    def __contains__(self, item):
        return item in self._data

    def save(self):
        with self.path.open("r") as f:
            data = f.readlines()

        output = []

        for line in data:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                output.append(line)
                continue

            eq_index = line.find("=")
            key = line[:eq_index]
            if key in self._changed_keys:
                output.append(f"{key}={self._data[key]}")
                self._changed_keys.remove(key)
                continue

            output.append(line)

        for key in self._changed_keys:
            output.append(f"{key}={self._data[key]}")

        with self.path.open("w") as f:
            for line in output:
                f.write(line)
                f.write("\n")

        self._changed_keys.clear()
