class Script(object):
    def __init__(self, action): #argobj={}):
        self.action = action
        self.target = None
        self.type = None
        #self.argobj = argobj
    def add(self):
        self.target.add_script(self)
    def remove(self):
        self.target.remove_script(self)
    def reset(self):
        pass
    def update(self):
        #if (len(self.argobj)):
        self.action()

class ScriptDelay(Script):
    def __init__(self, action, delay):
        self.origdelay = delay
        super(ScriptDelay, self).__init__(action)
        self.reset()
        
    def reset(self):
        self.delay = self.origdelay

    def update(self):
        if self.delay == 0:
            self.action()
            self.remove()
            return
        self.delay -= 1

class ScriptRepeat(ScriptDelay):
    def __init__(self, action, delay):
        super(ScriptRepeat, self).__init__(action, delay)
        self.delay = 0

    def update(self):
        if self.delay == 0:
            self.action()
            self.reset()
            return
        self.delay -= 1

class ScriptWhen(Script):
    def __init__(self, action, cond):
        self.cond = cond
        super(ScriptWhen, self).__init__(action)
        
    def update(self):
        if self.cond():
            self.action()
            self.remove()

class ScriptWhenEver(ScriptWhen):
    def __init__(self, action, cond):
        super(ScriptWhenEver, self).__init__(action, cond)
        
    def update(self):
        if self.cond():
            self.action()
            
class ScriptCollision(ScriptWhenEver):
    def __init__(self, type, action):
        super(ScriptWhenEver, self).__init__(action, self.anycoll)
        self.type = type
        
    def anycoll(self):
        for e in self.target.scene.alltype(self.type):
            if self.target.collide(e.rect()):
                self.result = e
                return e
        
    def update(self):
        if self.cond():
            self.action(self.result) 
            
            
            
class State(object):
    def __init__(self):
        self.state = None
        self.transto = {}
        self.transfrom = {}
        self.target = None
        
    def onstate(self, st, func):
        if (st not in self.transto):
            self.transto[st] = []
        self.transto[st].append(func)

    def offstate(self, st, func):
        if (st not in self.transfrom):
            self.transfrom[st] = []
        self.transfrom[st].append(func)

    def tostate(self, newst):
        if self.state in self.transfrom:
            self.target.every(self.transfrom[self.state], lambda f: f())

        self.state = newst            

        if self.state in self.transto:
            self.target.every(self.transto[self.state], lambda f: f())

    def duringstate(self, st, sc):
        if sc in self.target.scripts:
            self.target.remove_script2(sc)
        self.onstate(st, sc.reset)
        self.onstate(st, sc.add)
        self.offstate(st, sc.remove)