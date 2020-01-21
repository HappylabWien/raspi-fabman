import datetime, threading, time

next_call = time.time()

def foo():
  global next_call
  print datetime.datetime.now()
  next_call = next_call+1
  threading.Timer( next_call - time.time(), foo ).start()

foo()

print "HUGO"