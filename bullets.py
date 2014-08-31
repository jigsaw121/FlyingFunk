# -*- coding: UTF-8 -*- 
import flyingfunk as ff
import pygame, math, random
random.seed()

class Spellcard(ff.Scene):
    def spawn(self):
        self.add(Boss(160,120)) 
        self.add(Player(160,200))
        self.game.bgcolor = ff.Color(128,200,64)
        
        tracker = self.add(ff.Jammer())
        tracker.type = "tracker"
        tracker.when(lambda: tracker.tapped(pygame.K_ESCAPE), self.endgame)
        tracker.when(lambda: tracker.tapped(pygame.K_r), self.reset)
        tracker.whenever(lambda: tracker.tapped(pygame.K_f), lambda: self.announce(str(self.frame)))
        
class Bullet(ff.Jammer):
    def __init__(self, x, y, dx, dy): 
        super(Bullet, self).__init__()
        self.dims(x,y,4,4)
        self.x-=self.w/2; self.y-=self.h/2
        self.push(dx,dy)
        self.add_graphic(self.circlegfx(3, ff.Color(224,224,160)))
        #self.show_hitbox(ff.Color(224,160,128))
        self.type = "bullet"
            
    def scriptinit(self):
        self.when(self.oob, self.die)
    
    def stateinit(self):
        self.duringstate("active", self.always(self.movex))
        self.duringstate("active", self.always(self.movey))
        
        def blink():
            self.add_graphic(self.rectgfx(self.w, self.h, ff.Color(180,32,90)), "blink")
            self.delay(30, lambda: self.remove_graphic("blink"))  
        self.onstate("killer", lambda: self.setter("layer", 10))
        self.duringstate("killer", self.repeat(60, blink))
        
        self.tostate("active")
    
class Boss(ff.Jammer):
    def __init__(self, x, y): 
        super(Boss, self).__init__()
        self.dims(x,y,4,4)
        self.x-=self.w/2; self.y-=self.h/2
        self.show_hitbox(ff.Color(224,224,160))
        
        self.angle = math.pi*3/4

    def scriptinit(self):
        def attackinit(): 
            self.speed = 0.25; self.turnspeed = 0.5
        def spin(): 
            self.angle += self.turnspeed
            if self.speed<0.8: self.speed += 0.005
        self.onstate("attack1", attackinit)
        self.duringstate("attack1", self.always(spin))
        self.duringstate("attack1", self.repeat(1, lambda: self.shoot(self.speed)))
        
        self.onstate("attack1", lambda: self.delay(60*3, lambda: self.tostate("idle")))
        self.onstate("idle", lambda: self.delay(60*3, lambda: self.tostate("attack1")))
        
        self.tostate("attack1")
    
    def shoot(self, speed=1):
        self.scene.add(Bullet(self.x+self.w/2, self.y+self.h/2, math.cos(self.angle)*speed, math.sin(self.angle)*speed))

class Player(ff.Jammer):
    def __init__(self, x, y): 
        super(Player, self).__init__()
        self.dims(x,y,4,4)
        self.x-=self.w/2; self.y-=self.h/2
        self.layer = 32
        self.show_hitbox(ff.Color(32,180,90))
        
    def scriptinit(self):
        self.always(self.ctrl)
        self.always(self.movex); self.always(self.movey)
        self.constrain((0,0,self.scene.game.scr_w, self.scene.game.scr_h))

        self.oncollision("bullet", self.postgame)
        
    def postgame(self, hit):
        laugh_sfx = pygame.mixer.Sound("se_fault.wav")
        laugh_sfx.set_volume(0.3)
        laugh_sfx.play()
        score = self.scene.frame
        hit.tostate("killer")
        self.scene.pause(unless=[hit,"tracker","annc"])
        self.scene.announce("Zannen nagara")
        hit.delay(60, lambda: self.scene.announce("You lasted "+str(score)+" frames", -1))
        hit.delay(160, lambda: self.scene.announce("Press R or Esc...", -1))

    def constrain(self, (rx,ry,rw,rh)):
        def constfunc():
            if (self.x<rx): self.x=rx
            elif (self.x+self.w>rw): self.x=rw-self.w
            if (self.y<ry): self.y=ry
            elif (self.y+self.h>rh): self.y=rh-self.h
        return self.always(constfunc)
    
    def ctrl(self):
        self.dx = 0; self.dy = 0
        if self.held(pygame.K_UP): self.dy -= 1
        if self.held(pygame.K_DOWN): self.dy += 1
        if self.held(pygame.K_LEFT): self.dx -= 1
        if self.held(pygame.K_RIGHT): self.dx += 1        
        
game = ff.Game()
game.show(320,240,2)
game.set_scene(Spellcard())

game.play()