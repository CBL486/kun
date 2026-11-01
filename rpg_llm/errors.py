"""Typed LLM gateway errors."""


class LlmGatewayError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProviderError(LlmGatewayError):
    def __init__(self, message: str, *, transient: bool = True):
        super().__init__("provider_error", message)
        self.transient = transient


class ProviderUnavailable(ProviderError):
    def __init__(self, message: str = "模型供应商未配置"):
        super().__init__(message, transient=False)
        self.code = "provider_unavailable"


class ReviewUnavailable(LlmGatewayError):
    def __init__(self, message: str = "审核服务不可用"):
        super().__init__("review_unavailable", message)
