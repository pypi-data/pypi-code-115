import threading
import queue


class Thread_Api:
    def __init__(self, item_list, func, threadNum=5, queue_order=1):
        """
        :param item_list: 并发对象列表
        :param func: 工作函数对象
        :param threadNum: 并发数，默认 5
        :param queue_order: 0或1，先进先出/后进先出, 默认为1
        """
        self.item_list = item_list
        self.func = func
        self.queue_order = queue_order
        if queue_order:
            self.q = queue.Queue()  # 先进先出
        else:
            self.q = queue.LifoQueue()  # 后进先出
        self.threadNum = threadNum
        self.lock = threading.Lock()

    def worker(self):
        while not self.q.empty():
            item = self.q.get_nowait()  # 获得任务
            # with self.lock:
            self.func(item)

    def main(self):
        threads = []
        for task in self.item_list:
            self.q.put_nowait(task)
        for i in range(self.threadNum):
            thread = threading.Thread(target=self.worker)
            thread.setDaemon(True)  # 设置守护进程
            thread.start()
            threads.append(thread)
        for thread in threads:  # 线程阻塞
            thread.join()


if __name__ == '__main__':
    pass
