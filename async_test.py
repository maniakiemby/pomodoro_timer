from collections import deque
from asyncio import sleep


def first_coro_method():
    print(1)
    yield
    print(2)
    print(3)
    yield
    print(3)
    print(3)


def second_coro_method():
    print('aa')
    yield
    print('bb')
    print('bb')
    yield
    print('cc')
    print('cc')


if __name__ == "__main__":
    my_queue = deque()
    my_queue.appendleft(first_coro_method())
    my_queue.appendleft(second_coro_method())
    while True:
        try:
            current_coro = my_queue.pop()
            if current_coro:
                try:
                    next(current_coro)
                except StopIteration as e:
                    pass
                else:
                    my_queue.appendleft(current_coro)

        except IndexError as x:
            sleep(0.1)
        except Exception as x:
            pass
