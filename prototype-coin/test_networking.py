import asyncio    

loop = asyncio.get_event_loop()

async def slip(time):
  
  await asyncio.sleep(time)
  print(f'finished {time}')
  return 'hello'

async def main():
  total = [(i, asyncio.create_task(slip(i))) for i in range(1, 20, 3)]
  
  tasks = [task[1] for task in total]
  
  done, pending = await asyncio.wait(tasks, timeout=2)
  
  for task in pending:
      task.cancel()
      
  temp_total = total.copy()
  for task in temp_total:
    if not task[1] in done:
      total.remove(task)
      # print(f'Task {task[0]} is not cancelled :)')
      # print(task[1].result())

  for task in total:
    print(task[1].result())
    

if __name__ == '__main__':
    try:
        asyncio.run(main())
    
    except KeyboardInterrupt:
        print('Shutting Down...')
        loop.close()
  

