from datetime import datetime
import traceback

class Logger:
    def __init__(self, file_logging=False, path=".", max_file_size=None) -> None:
        self.file_logging = file_logging
        self.path = path
        self.max_file_size = max_file_size * 1024 * 1024 if max_file_size else max_file_size
        self.init_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def check_file_size(self) -> None:
        if self.max_file_size:
            try:
                f = open(f"{self.path}/{self.init_date}.log", "rb")
                content = f.read()
                size = len(content)
                if size >= self.max_file_size:
                    f.close()
                    f = open(f"{self.path}/{self.init_date}.log", "wb")
                    f.write(content[size - self.max_file_size + int(self.max_file_size/10):])
                    f.close()
            except:
                pass

    def info(self, data) -> None:
        now = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
        print(f"{now} \033[0;32mLOG :\033[0m {data}")
        if self.file_logging:
            self.check_file_size()
            with open(f"{self.path}/{self.init_date}.log", "a") as f:
                f.write(f"{now} \033[0;32mLOG :\033[0m {data}\n")

    def warn(self, data) -> None:
        now = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
        print(f"{now} \033[0;33mWARN :\033[0m {data}")
        if self.file_logging:
            self.check_file_size()
            with open(f"{self.path}/{self.init_date}.log", "a") as f:
                f.write(f"{now} \033[0;33mLOG :\033[0m {data}\n")

    def error(self, data, exc=None) -> None:
        now = datetime.now().strftime("[%Y-%m-%d - %H:%M:%S]")
        print(f"{now} \033[0;31mERROR :\033[0m {data}")
        if exc:
            print("".join(traceback.format_exception(exc)))
        if self.file_logging:
            self.check_file_size()
            with open(f"{self.path}/{self.init_date}.log", "a") as f:
                f.write(f"{now} \033[0;31mLOG :\033[0m {data}\n")
                if exc:
                    f.write("".join(traceback.format_exception(exc)))