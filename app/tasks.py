import time
def example(sec):
    print('Starting task')
    for i in (sec):
        print(i)
        time.sleep(1)
    print("Task completed")