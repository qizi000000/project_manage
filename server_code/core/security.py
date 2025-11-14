"""安全与认证相关工具函数（中文注释）。

包含：
- 密码哈希与校验（PBKDF2-SHA256，避免 bcrypt 在部分环境的兼容问题及 72 字节限制）
- JWT 令牌的创建与解析
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from core.config import settings

# 密码哈希上下文：使用 PBKDF2-SHA256 算法（纯 Python 实现，稳定可靠）
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希。"""
    return pwd_context.hash(password)


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    """创建访问令牌（JWT）。

    参数：
    - subject: 令牌主体（通常为用户 ID）
    - expires_minutes: 过期分钟数；未提供则使用配置中的默认值
    """
    to_encode = {"sub": subject}
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码并校验 JWT，返回 payload；失败则返回 None。"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
