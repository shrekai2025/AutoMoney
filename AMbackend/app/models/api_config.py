"""API Config Model - API配置表"""

from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime

from app.models.base import Base


class APIConfig(Base):
    """API配置表
    
    系统级API配置：
    - API基本信息
    - API密钥（加密存储）
    - API速率限制
    """
    __tablename__ = "api_config"

    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # API标识
    api_name = Column(String(100), unique=True, nullable=False, index=True,
                     comment="API唯一标识，如 'binance_api'")
    display_name = Column(String(200), nullable=False,
                         comment="显示名称，如 'Binance API'")
    description = Column(Text, comment="API描述")
    
    # API配置
    base_url = Column(String(500), comment="API基础URL")
    api_key_encrypted = Column(Text, comment="加密存储的API密钥")
    api_secret_encrypted = Column(Text, comment="加密存储的API密钥Secret（如果需要）")
    
    # 速率限制
    rate_limit = Column(Integer, comment="每分钟请求数限制")
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False, index=True,
                      comment="API状态")
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<APIConfig(id={self.id}, api_name={self.api_name}, display_name={self.display_name})>"

