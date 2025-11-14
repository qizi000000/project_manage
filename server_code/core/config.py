"""配置模块（中文注释）。

使用 pydantic-settings 从环境变量或 .env 文件中加载配置：
- 项目名称与 API 前缀
- JWT 安全相关参数
- 数据库连接地址（MySQL 异步驱动 aiomysql）
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置。

    优先级：环境变量 > .env 文件 > 默认值。
    """

    # 基础信息
    PROJECT_NAME: str = "ProjectManage API"  # 项目名称，用于 FastAPI 标题
    API_PREFIX: str = "/api"  # 统一的 API 路由前缀

    # 安全配置（JWT）
    SECRET_KEY: str = "change-me"  # 请在生产环境中修改为强随机字符串
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 令牌过期时间（分钟）
    ALGORITHM: str = "HS256"  # JWT 签名算法

    # 数据库 URL（异步 MySQL 示例：mysql+aiomysql://user:pass@host:port/dbname）
    DATABASE_URL: str = "mysql+aiomysql://root:root123456@localhost:3306/project_manage"

    class Config:
        env_file = ".env"  # 指定环境变量文件位置


settings = Settings()
