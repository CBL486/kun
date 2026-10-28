"""存储层类型化错误。"""


class StorageError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
