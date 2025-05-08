"""
日志系统模块
提供统一的日志记录功能
"""
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

class Logger:
    """日志管理类"""
    
    # 日志级别
    LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # 日志格式
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 单例实例
    _instance = None
    
    @classmethod
    def get_logger(cls, name='network_tools'):
        """获取日志记录器"""
        if cls._instance is None:
            cls._instance = cls._setup_logger(name)
        return cls._instance
    
    @classmethod
    def _setup_logger(cls, name):
        """设置日志记录器"""
        # 创建日志目录
        log_dir = os.path.join(os.path.expanduser('~'), '.network_tools', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建日志文件名
        log_file = os.path.join(log_dir, f'{name}_{datetime.now().strftime("%Y%m%d")}.log')
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(cls.FORMAT))
        
        # 创建文件处理器
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(cls.FORMAT))
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
    
    @classmethod
    def set_level(cls, level):
        """设置日志级别"""
        if cls._instance:
            level_value = cls.LEVELS.get(level.lower(), logging.INFO)
            cls._instance.setLevel(level_value)
            
            # 更新处理器级别
            for handler in cls._instance.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(level_value)


# 创建默认日志记录器
logger = Logger.get_logger()
