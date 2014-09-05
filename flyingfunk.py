# -*- coding: UTF-8 -*- 

import pygame, os
import behaviour as bhv
pygame.init()
os.chdir(os.path.dirname(os.path.realpath(__file__)))

class Game():
    # tietää globaalin tilan, mm. missä maailmassa ollaan
    def __init__(self): 
        self.scene = None
        self.screen = None
        self.bgcolor = Color(90,140,140)
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.keys = pygame.key.get_pressed()
        self.keystate = [[False, False] for f in self.keys]
        self.clicks = pygame.mouse.get_pressed()
        self.clickstate = [[False, False, None] for c in self.clicks]
        self.mousepos = pygame.mouse.get_pos()
        self.scale = 1
        print "Get this jam started"
    
    def set_scene(self, scene):
        self.scene = scene
        scene.game = self
        scene.reset()
        return scene

    def show(self, scr_w, scr_h, scale=1, windowx=0, windowy=0):
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (windowx,windowy)
        scale = int(scale)
        if scale==1:            
            self.screen = pygame.display.set_mode((scr_w*scale, scr_h*scale), pygame.NOFRAME|pygame.SRCALPHA, 32)
        elif (scale>1):
            self.screen = pygame.Surface((scr_w, scr_h))
            self.scaledscreen = pygame.display.set_mode((scr_w*scale, scr_h*scale), pygame.NOFRAME|pygame.SRCALPHA, 32)

        self.scr_w = scr_w; self.scr_h = scr_h
        self.scale = scale
        
    def updateinput(self):
        # nää "on painettu vaan kerran" -spedeilyt on ihan kaameita, millähän lie pygamen eventtihöskillä onnistuis paremmin
        pygame.event.get()
        self.mousepos = [p/self.scale for p in pygame.mouse.get_pos()]
        self.clicks = pygame.mouse.get_pressed()
        for c in range(len(self.clicks)):
            if self.clickstate[c][0]:
                self.clickstate[c][1] = False
                if not self.clicks[c]:
                    self.clickstate[c][0] = False
            else:
                if self.clicks[c]:
                    self.clickstate[c][1] = True
                    self.clickstate[c][0] = True
                else:
                    if self.clickstate[c][0]:
                        self.clickstate[c][0] = False
            self.clickstate[c][2] = None
        
        self.keys = pygame.key.get_pressed()
        for k in range(len(self.keys)):
            if self.keystate[k][0]:
                self.keystate[k][1] = False
                if not self.keys[k]:
                    self.keystate[k][0] = False
            else:
                if self.keys[k]:
                    self.keystate[k][1] = True
                    self.keystate[k][0] = True
                else:
                    if self.keystate[k][0]:
                        self.keystate[k][0] = False

    def play(self):
        while 1:
            if self.scene is None:
                # peli loppuu kun ei olla missään
                break
            self.clock.tick(self.fps)
            self.updateinput()
            if self.screen: self.screen.fill(self.bgcolor.render())

            self.scene.update()
            
            if (self.scale>1):
                pygame.transform.scale(self.screen, (self.scr_w*self.scale, self.scr_h*self.scale), self.scaledscreen)
            if self.screen: pygame.display.update()
            
        print "*applause*"
        pygame.quit()
    
class Camera():
    def __init__(self):
        self.x = 0; self.y = 0;

class Scene(object):
    def __init__(self):
        self.game = None

    def reset(self):
        self.frame = -1
        self.entities = []
        self.add_buffer = []
        self.remove_buffer = []
        self.camera = Camera()
        self.spawn()

    def add(self, newent):
        self.add_buffer.append(newent)
        newent.scene = self
        newent.birth()
        return newent

    def remove(self, oldent):
        self.remove_buffer.append(oldent)
        return oldent

    def remove2(self, oldent):
        if oldent in self.entities: 
            self.entities.remove(oldent)

    def spawn(self):
        # ylikirjoita tämä kaikilla maailman entiteeteillä
        pass

    def alltype(self, enttype):
        return self.sublist(self.entities, lambda e: e.type == enttype)

    def allclass(self, entclass):
        return self.sublist(self.entities, lambda e: isinstance(e, entclass))

    def every(self, obj, action):
        if (not hasattr(obj, "__iter__")):
            # voi olla stringi tai classi listan sijaan
            if isinstance(obj, basestring):
                obj = self.alltype(obj)
            else:
                obj = self.allclass(obj)

        if (not callable(action)):
            # jos string, kutsutaan metodia
            method = action
            action = lambda o: getattr(o, method)()

        for o in obj:
            action(o)
    
    def sublist(self, iter, proc):
        return [i for i in iter if proc(i)]
    
    def announce(self, msg, delay=140):
        annc = self.add(Jammer())
        annc.type = "annc"
        txt = annc.add_graphic(Text(msg, Color(224,224,224)))
        txt.parallax(0) # grafiikan sijainti riippumaton kamerasta
        def align(): annc.y = self.alltype("annc").index(annc)*txt.h
        annc.always(align)
        annc.delay(delay, annc.die)
    
    def change(self, newscene):
        self.game.scene = newscene

    def endgame(self):
        self.change(None)
        
    def pause(self, unless=None):
        if unless is None: unless = []
        
        def procfunc(exempt):
            if (isinstance(exempt, basestring)):
                return lambda obj: obj.type==exempt
            return lambda obj: obj==exempt
        unless = [procfunc(exempt) for exempt in unless]
        
        def entpause(ent, unless):
            for exempt in unless:
                if exempt(ent): return
            ent.pause()
        self.every(self.entities, lambda ent: entpause(ent, unless))
        self.every(self.add_buffer, lambda ent: entpause(ent, unless))
        
    def unpause(self):
        self.every(self.entities, "unpause")
        
    def update(self):
        self.frame+=1
        if (not self.entities and not self.add_buffer):
            print "DEBUG: No entities in active scene"
        
        self.every(self.add_buffer, lambda o: self.entities.append(o))
        self.every(self.remove_buffer, self.remove2)
        self.add_buffer = []
        self.remove_buffer = []

        self.entities.sort(key=lambda e: e.layer)
        for e in self.entities:
            e.update()
            if self.frame<0: return
        if self.game.screen is not None: 
            self.every(self.entities, "draw")
        
class Color():
    def __init__(self, r, g, b, a=255):
        self.r = r; self.g = g; self.b = b; self.a = a

    def render(self):
        self.r = self.r%256; self.g = self.g%256; self.b = self.b%256; self.a = self.a%256
        return (self.r, self.g, self.b, self.a)

class Graphic(object):
    loaded = {}
    def __init__(self, surface, type="unknown", offx=0, offy=0):
        self.x = offx; self.y = offy;
        self.type = type
        self.scroll = 1
        if isinstance(surface, basestring):
            surfid = surface
            if surfid in Graphic.loaded:
                surface = Graphic.loaded[surfid]
            else:
                surface = pygame.image.load(surfid).convert_alpha()
                Graphic.loaded[surfid] = surface
            
        self.surface = surface
        self.target = None
        self.w = surface.get_width()
        self.h = surface.get_height()
    
    def center(self):
        self.x = self.target.w/2-self.w/2
        self.y = self.target.h/2-self.h/2

    def parallax(self, p):
        self.scroll = p
    
    def draw(self):
        tx = -self.target.scene.camera.x*self.scroll+self.target.x+self.x
        ty = -self.target.scene.camera.y*self.scroll+self.target.y+self.y
        if (tx+self.w<0 or
            ty+self.h<0 or
            tx>=self.target.scene.game.scr_w or
            ty>=self.target.scene.game.scr_h):
            return

        self.target.scene.game.screen.blit(self.surface, (tx,ty))

class Text(Graphic):
    defaultfont = pygame.font.Font("04B_19__.TTF", 14)
    def __init__(self, msg, color, offx=0, offy=0, font=None):
        if font is None:
            font = Text.defaultfont 
        surface = font.render(msg, False, color.render())
        super(Text, self).__init__(surface, offx, offy)

class Jammer(object):
    def __init__(self):
        self.x = 0; self.y = 0
        self.dx = 0; self.dy = 0
        self.w = 16; self.h = 16
        self.type = "unknown"
        self.layer = 0
        self.scene = None

        self.scripts = []
        self.state = None
        self.temp = {}
        self.graphics = []
        self.active = True

        self.scremove_buffer = []

    def imginit(self): pass
    def stateinit(self): pass
    def scriptinit(self): pass

    def birth(self):
        self.state = bhv.State()
        self.state.target = self
        self.imginit()
        self.stateinit()
        self.scriptinit()

    def dims(self,x,y,w,h,center=False):
        self.x = x; self.y = y; self.w = w; self.h = h
        if center:
            self.x-=self.w/2; self.y-=self.h/2
    def push(self,dx,dy):
        self.dx += dx; self.dy += dy
    
    def instate(self):
        return self.state.state
    def onstate(self, st, func):
        self.state.onstate(st, func)
    def offstate(self, st, func):
        self.state.offstate(st, func)
    def tostate(self, st):
        self.state.tostate(st)
    def duringstate(self, st, sc):
        self.state.duringstate(st, sc)
    
    def add_script(self, sc):
        self.scripts.append(sc)
        sc.target = self
        return sc
    def remove_script(self, sc):
        if (sc not in self.scremove_buffer): 
            self.scremove_buffer.append(sc)
    def remove_script2(self, sc):
        if (sc in self.scripts):
            self.scripts.remove(sc)
        else:
            print "DEBUG: Tried to remove non-existing "+str(sc)+" from "+str(self)
    def remove_script_type(self, scid):
        for sc in self.scripts:
            if sc.type == scid:
                self.remove_script(sc)
                
    def always(self, func):
        return self.add_script(bhv.Script(func))
    def delay(self, delay, func):
        return self.add_script(bhv.ScriptDelay(func, delay))
    def repeat(self, delay, func):
        return self.add_script(bhv.ScriptRepeat(func, delay))
    def when(self, cond, func):
        return self.add_script(bhv.ScriptWhen(func, cond))
    def whenever(self, cond, func):
        return self.add_script(bhv.ScriptWhenEver(func, cond))
    def onhover(self, func):
        return self.whenever(self.hover, func)
    def onclick(self, func):
        return self.whenever(self.clicked, func)
    def oncollision(self, type, func):
        return self.add_script(bhv.ScriptCollision(type, func))
    
    def every(self, obj, action):
        self.scene.every(obj, action)
    def sublist(self, iter, proc):
        return self.scene.sublist(iter, proc)
       
    def rect(self):
        # NOTE: höpsöä tehdä tää pygamen rectien avulla ja luoda uus rect joka kerta
        return pygame.Rect(-self.scene.camera.x+self.x, -self.scene.camera.y+self.y, self.w, self.h)
       
    def collide(self, rect):
        return self.rect().colliderect(rect)
    
    def oob(self):
        # out of bounds
        return (self.x+self.w < 0 or
                self.y+self.h < 0 or
                self.x >= self.scene.game.scr_w or
                self.y >= self.scene.game.scr_h)

    def add_graphic(self, gfx, gfid=None):
        self.graphics.append(gfx)
        if gfid: gfx.type = gfid
        gfx.target = self
        return gfx
    def remove_graphic(self, gfid):
        count = len(self.graphics)
        self.graphics = self.sublist(self.graphics, lambda g: not g.type==gfid)
        if len(self.graphics)==count:
            print "DEBUG: Tried to remove non-existing "+gfid+" from "+str(self)
    def gfxfind(self, gfid):
        for g in self.graphics:
            if g.type==gfid:
                return g
    def gfxtype(self, gfid):
        return self.sublist(self.graphics, lambda g: g.type==gfid)
    
    def rectgfx(self, w, h, color=None):
        rc = pygame.Surface((w, h), pygame.SRCALPHA, 32)
        if color is None: 
            color = Color(224,224,224)
        rc.fill(color.render())
        return Graphic(rc)
    def circlegfx(self, rad, color=None):
        crc = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA, 32)
        if color is None: 
            color = Color(224,224,224)
        pygame.draw.circle(crc, color.render(), (rad, rad), rad)
        gfx = Graphic(crc)
        gfx.target = self
        gfx.center()
        return gfx
    
    def show_hitbox(self, color=None):
        self.add_graphic(self.rectgfx(self.w, self.h, color), "hitbox")

    def hover(self):
        return self.rect().collidepoint(self.scene.game.mousepos[0], self.scene.game.mousepos[1])
    def clicked(self):
        if self.scene.game.clickstate[0][1] and self.hover():
            if self.scene.game.clickstate[0][2] in [None, self]:
                self.scene.game.clickstate[0][2] = self   # blokkaa muut klikattavat
                return True
        return False
    def held(self, keyid):
        return self.scene.game.keys[keyid]
    def tapped(self, keyid):
        return self.scene.game.keystate[keyid][1]
    
    def movex(self):
        self.x += self.dx
    def movey(self):
        self.y += self.dy
        
    def pause(self): self.active = False
    def unpause(self): self.active = True

    def die(self):
        self.scene.remove(self)

    def draw(self):
        self.every(self.graphics, "draw")
        
    def setter(self, varname, val):
        setattr(self, varname, val)
    def getter(self, varname):
        return getattr(self, varname)

    def update(self):
        # älä ylikirjoita periessä! lisää vain uusia skriptejä
        if not self.active:
            return
        self.every(self.scripts, "update")
        self.every(self.scremove_buffer, self.remove_script2)
        self.scremove_buffer = []
