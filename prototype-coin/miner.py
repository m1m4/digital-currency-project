import time
from hashlib import *
from multiprocessing import *

from block import *


def timer(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
        return result
    return wrap_func


def found(value, difficulty):
    val_hash = sha256(value.encode()).hexdigest()
    # print(f'{value}: {hash}')
    if val_hash.startswith(''.zfill(difficulty)):
        return True
    else:
        return False


def find(offset, difficulty, queue):

    print('e o e  o')
    count = offset
    value = ''

    found_ = False
    while not found_:
        if found(value, difficulty):
            print('Found!')
            queue.put_nowait(value)
            return value

        value = str(count)
        count += cpu_count()

    print('Not found')
    return None


def callback(result):
    for res in result:
        print(f'Found at {res} : {sha256(res.encode()).hexdigest()}')


def foo(x1, q):
    print('adding to queue ' + str(x1))
    q.put(str(x1))
    print('adding to queue ' + str(x1 * 2))
    q.put(str(x1 * 2))


def main():
    pool = Pool()

    # difficulty = int(input('Enter difficulty... '))
    difficulty = 4

    res_queue = Queue(cpu_count())

    # process_results = []
    params_list = [(i, difficulty, res_queue) for i in range(cpu_count())]
    print(params_list)

    # pool.starmap_async(foo, [(1, res_queue), (3, res_queue)])

    # processes = []
    # for i in range(2):
    #     processes.append(Process(target=foo, args=(i, res_queue)))
    #     print(f'foo({i}, {res_queue})')
    #     processes[i].start()

    p = Process(target=foo, args=(3, res_queue))
    p.start()

    # print(res_queue.get(True, timeout=5))

    p.join()

    print(res_queue.empty())
    while not res_queue.empty():
        print(res_queue.get(True, 5))

    # for p in processes:
    #     p.join()

    p.join()
    print('Finished')


if __name__ == "__main__":
    main()
