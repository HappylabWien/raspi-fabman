import threading

def hello_world():
        print 'Hello!'
        threading.Timer(2,hello_world).start()

if __name__ == "__main__":
    try:
        hello_world()
    except KeyboardInterrupt:
        print '\nGoodbye!'
    print "main thread exited"