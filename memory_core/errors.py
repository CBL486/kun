"""记忆核心类型化错误。"""


class MemoryCoreError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ScopeError(MemoryCoreError):
    def __init__(self, message: str = "记忆作用域不匹配"):
        super().__init__("scope_mismatch", message)


class ValidationError(MemoryCoreError):
    def __init__(self, message: str):
        super().__init__("validation_error", message)


class ConflictError(MemoryCoreError):
    def __init__(self, message: str = "记忆去重键内容冲突"):
        super().__init__("conflict", message)


class NotFoundError(MemoryCoreError):
    def __init__(self, message: str = "记忆不存在"):
        super().__init__("not_found", message)
