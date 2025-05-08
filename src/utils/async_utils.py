"""
异步处理工具模块
提供异步任务处理的工具类和函数
"""
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Callable, Any, Dict, Optional, Tuple

class AsyncTask(QThread):
    """异步任务处理类"""
    
    # 任务完成信号，返回结果和可选的错误信息
    task_completed = pyqtSignal(object, object)
    
    def __init__(self, task_func: Callable, *args, **kwargs):
        """
        初始化异步任务
        
        Args:
            task_func: 要执行的任务函数
            *args: 传递给任务函数的位置参数
            **kwargs: 传递给任务函数的关键字参数
        """
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.error = None
    
    def run(self):
        """执行任务"""
        try:
            self.result = self.task_func(*self.args, **self.kwargs)
            self.task_completed.emit(self.result, None)
        except Exception as e:
            self.error = e
            self.task_completed.emit(None, str(e))


class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        self.tasks = {}
    
    def run_task(self, task_id: str, task_func: Callable, 
                 callback: Callable[[Any, Optional[str]], None], 
                 *args, **kwargs) -> None:
        """
        运行异步任务
        
        Args:
            task_id: 任务ID，用于标识和管理任务
            task_func: 要执行的任务函数
            callback: 任务完成后的回调函数，接收结果和错误信息
            *args: 传递给任务函数的位置参数
            **kwargs: 传递给任务函数的关键字参数
        """
        # 如果已有同ID任务在运行，先停止它
        self.stop_task(task_id)
        
        # 创建新任务
        task = AsyncTask(task_func, *args, **kwargs)
        task.task_completed.connect(
            lambda result, error: self._on_task_completed(task_id, result, error, callback)
        )
        
        # 保存任务并启动
        self.tasks[task_id] = task
        task.start()
    
    def stop_task(self, task_id: str) -> None:
        """
        停止指定ID的任务
        
        Args:
            task_id: 要停止的任务ID
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if task.isRunning():
                task.terminate()
                task.wait()
            del self.tasks[task_id]
    
    def stop_all_tasks(self) -> None:
        """停止所有任务"""
        for task_id in list(self.tasks.keys()):
            self.stop_task(task_id)
    
    def _on_task_completed(self, task_id: str, result: Any, 
                          error: Optional[str], callback: Callable) -> None:
        """
        任务完成处理
        
        Args:
            task_id: 任务ID
            result: 任务结果
            error: 错误信息
            callback: 回调函数
        """
        # 从任务列表中移除
        if task_id in self.tasks:
            del self.tasks[task_id]
        
        # 调用回调函数
        if callback:
            callback(result, error)
