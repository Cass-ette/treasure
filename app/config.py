import os

class Config:
    SECRET_KEY = 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 定时任务配置
    FUND_NAV_UPDATE_TIME = '18:00'  # 每日更新基金净值的时间
    
    # 基金净值获取配置
    USE_AKSHARE = True  # 是否使用akshare库获取数据