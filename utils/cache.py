"""
缓存管理模块
包含本地缓存目录的创建、清理等功能
"""
import os


def get_cache_folder():
    """获取本地缓存文件夹"""
    cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir


def clear_cache():
    """清空缓存文件夹"""
    cache_dir = get_cache_folder()
    for filename in os.listdir(cache_dir):
        filepath = os.path.join(cache_dir, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
        except:
            pass
