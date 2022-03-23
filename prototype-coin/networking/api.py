from fastapi import FastAPI
import asyncio
import threading
import time
import typing

import requests
from requests.adapters import HTTPAdapter
import uvicorn

from uvicorn.config import Config
from uvicorn.main import Server


app = FastAPI()

@app.get('/')
def home():
    return {'banan': 'ok'}


def test_run_signal_multi_threads(app, threads_count= 10):

    def join_t(*threads: threading.Thread) -> typing.List[None]:
        return [t.join() for t in threads]

    def start_threads(*threads: threading.Thread) -> typing.List[None]:
        return [t.start() for t in threads]

    def event_thread(
        worker: typing.Awaitable, loop, *args, **kwargs
    ) -> threading.Thread:
        def _worker(*args, **kwargs):
            try:
                loop.run_until_complete(worker(*args, **kwargs))
            except Exception as e:
                print(e)
            finally:
                loop.close()

        return threading.Thread(target=_worker, args=args, kwargs=kwargs)

    
    loops = [asyncio.new_event_loop() for i in range(threads_count)]
    for loop in loops:
        asyncio.set_event_loop(loop)
    configs = [
        Config(
            app=app,
            port=10000 + i,
            loop=loops[i],
            limit_max_requests=1,
        )
        for i in range(threads_count)
    ]
    
    servers = [Server(config=configs[i]) for i in range(threads_count)]
    workers = [event_thread(servers[i].serve, loop=loops[i]) \
               for i in range(threads_count)]
    
    start_threads(*workers)
    time.sleep(1)
    
    for x in range(threads_count):
        port = 10000 + x
        s = requests.Session()
        s.mount(f"http://127.0.0.1:{port}", HTTPAdapter(max_retries=1))
        response = s.get(f"http://127.0.0.1:{port}")
        assert response.status_code == 204
        
    join_t(*workers)



def run_in_parallel(app, func, *args, **kwargs):
    def join_t(*threads: threading.Thread) -> typing.List[None]:
        return [t.join() for t in threads]

    def start_threads(*threads: threading.Thread) -> typing.List[None]:
        return [t.start() for t in threads]

    def event_thread(
        worker: typing.Awaitable, loop, *args, **kwargs
    ) -> threading.Thread:
        def _worker(*args, **kwargs):
            try:
                loop.run_until_complete(worker(*args, **kwargs))
            except Exception as e:
                print(e)
            finally:
                loop.close()

        return threading.Thread(target=_worker, args=args, kwargs=kwargs)

    
    # Server and function event loops
    server_loop = asyncio.new_event_loop()
    func_loop = asyncio.new_event_loop()
    
    # Set event loops
    asyncio.set_event_loop(server_loop)
    asyncio.set_event_loop(func_loop)
    
    # Server config
    server_config = Config(app=app, port=10000, loop=server_loop,
                           limit_max_requests=1)
    
    server = Server(config=server_config)
    
    
    server_worker = event_thread(server.serve, loop=server_loop)
    func_worker = event_thread(func, func_loop, *args, **kwargs)
    
    start_threads(server_worker, func_worker)
    time.sleep(1)
        
    join_t(server_worker, func_worker)



async def func(name):
    print(f'hello {name}')
    

if __name__ == "__main__":
    
    
    # server_procces = multiprocessing.Process(target=uvicorn.run(app, host='localhost', port=9999))
    # server_procces.start()
    
    uvicorn.run
    run_in_parallel(app, func, 'mima')