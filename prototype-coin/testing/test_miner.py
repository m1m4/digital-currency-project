import asyncio
import multiprocessing as mp
import random
import time
from concurrent.futures import ProcessPoolExecutor
from node import Node
import dill
import websockets
import blockchain
import wallet

from miner import Miner

                    
async def func_async(num: int):
    print(f'PID {mp.current_process().pid}: Async function: waiting...')
    await asyncio.sleep(2)
    print(f'PID {mp.current_process().pid}: Async function: got answer')
    return num * 2

def cpu_heavy(finished_event):
    
    print(f'PID {mp.current_process().pid}: Started cpu heavy process...')
    
    num = random.randint(1, 50)
    while not num == 10:
        if finished_event.is_set():
            print(f'PID {mp.current_process().pid}: Cancelled')
            return
        
        time.sleep(0.5)
        num = random.randint(1, 50)
    print(f'PID {mp.current_process().pid}: Finished cpu heavy process.')
    return num

async def handle(block):
    print('Block processed!!!! .......')
           
           
            
async def echo(websocket):
    
    print(dill.pickles(websocket))
    async for message in websocket:
        await websocket.send(message)

async def main():
    e = mp.Event()
    print(dill.pickles(e))
    e.set()
    print(dill.pickles(e))

if __name__ == "__main__":
    e = mp.Event()
    print(dill.pickles(e))
    e.set()
    print(dill.pickles(e))
