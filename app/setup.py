"""Private DeepSeek setup state and credential storage."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import httpx


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
KEY_FILE_NAME = "deepseek_api_key.txt"
STATE_FILE_NAME = "setup_state.json"
LOCK_FILE_NAME = ".setup.lock"


class SetupError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
    ):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class SetupStatus:
    configured: bool
    provider: str
    key_hint: str | None
    persona_configured: bool
    world_ready: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured": self.configured,
            "provider": self.provider,
            "key_hint": self.key_hint,
            "persona_configured": self.persona_configured,
            "world_ready": self.world_ready,
        }


class DeepSeekValidator:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        base_url: str = DEEPSEEK_BASE_URL,
        timeout_seconds: float = 15.0,
    ):
        self.client = client or httpx.Client(timeout=timeout_seconds)
        self.base_url = base_url.rstrip("/")

    def validate(self, api_key: str) -> None:
        try:
            response = self.client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
        except httpx.TimeoutException as error:
            raise SetupError(
                "deepseek_timeout",
                "DeepSeek 校验超时",
                status_code=504,
            ) from error
        except httpx.HTTPError as error:
            raise SetupError(
                "deepseek_network_error",
                "无法连接 DeepSeek",
                status_code=503,
            ) from error
        if response.status_code in {401, 403}:
            raise SetupError(
                "deepseek_auth_failed",
                "DeepSeek Key 无效或没有权限",
                status_code=422,
            )
        if response.status_code in {402, 429}:
            raise SetupError(
                "deepseek_quota_unavailable",
                "DeepSeek 额度不足或请求过于频繁",
                status_code=429,
            )
        if response.status_code >= 500:
            raise SetupError(
                "deepseek_unavailable",
                "DeepSeek 当前不可用",
                status_code=503,
            )
        if response.status_code >= 400:
            raise SetupError(
                "deepseek_request_rejected",
                "DeepSeek 拒绝了校验请求",
                status_code=422,
            )
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as error:
            raise SetupError(
                "deepseek_invalid_response",
                "DeepSeek 返回了无法解析的响应",
                status_code=502,
            ) from error
        if not isinstance(payload, dict) or not isinstance(
            payload.get("data"),
            list,
        ):
            raise SetupError(
                "deepseek_invalid_response",
                "DeepSeek 校验响应结构不完整",
                status_code=502,
            )


class DeepSeekSetupStore:
    provider = "deepseek"

    def __init__(
        self,
        root: Path | str,
        *,
        secure_acl: bool = False,
        lock_timeout_seconds: float = 5.0,
    ):
        self.root = Path(root).resolve()
        self.secure_acl = secure_acl
        self.lock_timeout_seconds = lock_timeout_seconds
        self._guard = threading.RLock()
        self._acl_applied = False
        self.root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_settings(cls, settings: Any) -> "DeepSeekSetupStore":
        configured = getattr(settings, "setup_directory", None)
        root = Path(configured) if configured else Path.cwd() / "data" / "setup"
        return cls(
            root,
            secure_acl=bool(getattr(settings, "enforce_setup_acl", True)),
        )

    @property
    def key_path(self) -> Path:
        return self.root / KEY_FILE_NAME

    @property
    def state_path(self) -> Path:
        return self.root / STATE_FILE_NAME

    def status(self) -> SetupStatus:
        with self._guard:
            key = self._read_key()
            state = self._read_state()
            configured = bool(key)
            return SetupStatus(
                configured=configured,
                provider=self.provider,
                key_hint=self._hint(key) if key else None,
                persona_configured=bool(state.get("persona_configured")),
                world_ready=bool(
                    configured
                    and state.get("world_ready")
                    and state.get("persona_configured")
                ),
            )

    def validate_key(self, api_key: str, validator: DeepSeekValidator) -> None:
        normalized = self._normalize_key(api_key)
        validator.validate(normalized)

    def save_key(self, api_key: str, validator: DeepSeekValidator) -> SetupStatus:
        normalized = self._normalize_key(api_key)
        with self._file_lock():
            validator.validate(normalized)
            if self.secure_acl and not self._acl_applied:
                self._restrict_windows_acl()
                self._acl_applied = True
            self._atomic_write(self.key_path, normalized + "\n")
            state = self._read_state()
            state.update(
                {
                    "provider": self.provider,
                    "configured_at": _utc_now(),
                    "key_hint": self._hint(normalized),
                }
            )
            self._atomic_write(
                self.state_path,
                json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            )
            return self.status()

    def complete(self, *, persona_configured: bool) -> SetupStatus:
        with self._file_lock():
            status = self.status()
            if not status.configured:
                raise SetupError(
                    "deepseek_not_configured",
                    "请先保存有效的 DeepSeek Key",
                    status_code=409,
                )
            if not persona_configured:
                raise SetupError(
                    "persona_not_configured",
                    "请先选择默认人设或保存自定义人设",
                    status_code=409,
                )
            state = self._read_state()
            state["persona_configured"] = True
            state["world_ready"] = True
            state["completed_at"] = _utc_now()
            self._atomic_write(
                self.state_path,
                json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            )
            return self.status()

    def clear_key(self) -> SetupStatus:
        with self._file_lock():
            if self.key_path.exists():
                self.key_path.unlink()
            state = self._read_state()
            state["world_ready"] = False
            state.pop("key_hint", None)
            self._atomic_write(
                self.state_path,
                json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
            )
            return self.status()

    def _read_key(self) -> str | None:
        try:
            value = self.key_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return value or None

    def _read_state(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _normalize_key(api_key: str) -> str:
        normalized = api_key.strip()
        if (
            len(normalized) < 12
            or len(normalized) > 256
            or any(character.isspace() for character in normalized)
        ):
            raise SetupError(
                "invalid_deepseek_key",
                "DeepSeek Key 格式无效",
                status_code=422,
            )
        return normalized

    @staticmethod
    def _hint(api_key: str) -> str:
        return f"{api_key[:3]}...{api_key[-4:]}"

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)

    @contextmanager
    def _file_lock(self) -> Iterator[None]:
        lock_path = self.root / LOCK_FILE_NAME
        deadline = time.monotonic() + self.lock_timeout_seconds
        descriptor = None
        while descriptor is None:
            try:
                descriptor = os.open(
                    lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
            except FileExistsError:
                try:
                    stale = time.time() - lock_path.stat().st_mtime > 30
                except OSError:
                    stale = False
                if stale:
                    lock_path.unlink(missing_ok=True)
                    continue
                if time.monotonic() >= deadline:
                    raise SetupError(
                        "setup_lock_busy",
                        "另一个设置进程正在写入，请稍后重试",
                        status_code=409,
                    )
                time.sleep(0.05)
        try:
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.close(descriptor)
            descriptor = None
            yield
        finally:
            if descriptor is not None:
                os.close(descriptor)
            lock_path.unlink(missing_ok=True)

    def _restrict_windows_acl(self) -> None:
        if os.name != "nt":
            return
        user = os.environ.get("USERNAME")
        if not user:
            raise SetupError(
                "setup_acl_failed",
                "无法确定当前服务账户，不能保护 Key 文件",
                status_code=503,
            )
        grants = [
            f"{user}:(OI)(CI)F",
            "SYSTEM:(OI)(CI)F",
            "Administrators:(OI)(CI)F",
        ]
        command = [
            "icacls",
            str(self.root),
            "/inheritance:r",
            "/grant:r",
            *grants,
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise SetupError(
                "setup_acl_failed",
                "无法为 Key 文件设置私有访问权限",
                status_code=503,
            )


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
