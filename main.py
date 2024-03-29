
from functools import total_ordering
import pygame, sys, random
import numpy as np
import csv
import math
from time import sleep

import time
import asyncio

from pygame.locals import *

#import aws
UID = 'e793419b-17db-4938-a719-db8bcb929225'
NAME = 'Eric Zhang'


pygame.init()

clock = pygame.time.Clock()
fps = 60
start_time = pygame.time.get_ticks()

level = 1
TOTAL_LEVELS = 2
levelcooldown = True # for updating the level, true = can upgrade
ROWS = 16
COLS = 166
spawn = [0, 0]


#colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)



screen_width = 800
screen_height = int(screen_width * 0.8)
tile_size = screen_height // ROWS
levelProgress = [0, 0]


SCROLL_THRESH = 200

level_length = (COLS - 1) * tile_size


decorations = 0

screenshake = 0

fadeAm = (screen_height / 2) + 200
fadeCounter = screen_height / 2

screen_scroll = [0, 0]

bg_scroll = 0

hold1 = False
hold2 = False
hold3 = False
hold4 = False



screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Test')

game_over = 0

# load images
pine1_img = pygame.image.load('backgrounds/pine/pine1.png').convert_alpha()
pine2_img = pygame.image.load('backgrounds/pine/pine2.png').convert_alpha()
sky_img = pygame.image.load('backgrounds/pine/sky_cloud.png').convert_alpha()
mountain_img = pygame.image.load('backgrounds/pine/mountain.png').convert_alpha()
spell_slot = pygame.image.load('assets/gui/spell_bg.png').convert_alpha()
spell_slot = pygame.transform.scale(spell_slot,(52, 52))
# store tiles in a list
TILE_TYPES = 11
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'tiles/{x}.png')
    img = pygame.transform.scale(img, (tile_size, tile_size))
    img_list.append(img)


projectile_img = pygame.image.load('assets/spell_assets/projectile1.png').convert_alpha()

energy_img = pygame.image.load('energysymbol_bg.png').convert_alpha()
energy_img = pygame.transform.scale(energy_img, (49, 49))

health_img = pygame.image.load('health.png').convert_alpha()
health_img = pygame.transform.scale(health_img, (44, 44))





def draw_bg():
    for x in range(5):
        width = sky_img.get_width()
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))

        screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, screen_height - mountain_img.get_height() - 300))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, screen_height - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, screen_height - pine2_img.get_height()))

#reset level
def reset_level(level):
    world= World()
    world_data = []
    for row in range(ROWS):
        r = [-1] * COLS
        world_data.append(r)

    end_group.empty()
    projectile_group.empty()
    collectible_group.empty()
    zombie_group.empty()
    dead_group.empty()
    with open(f'levels/level{level}_data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for x, row in enumerate(reader):
            for y, tile in enumerate(row):
                world_data[x][y] = int(tile)
    
    world.process_data(world_data)
    
    return world
    

class World():
    def __init__(self):
        self.obstacle_list = []



    def process_data(self, data):
        self.level_length = len(data[0])
        
        # iterate through each value in file
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile == 100:
                    spawn[0] = x * tile_size
                    spawn[1] = y * tile_size
                    levelProgress[0] = spawn[0]
                    levelProgress[1] = spawn[1]



                if tile >= 0 and tile <= 10:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * tile_size
                    img_rect.y = y * tile_size
                    tile_data = (img, img_rect)
                    self.obstacle_list.append(tile_data)   

                elif tile == 11:
                    # enemy

                    zombie = Enemy(x * tile_size, y * tile_size)
                    zombie_group.add(zombie)
                    pass

                elif tile == 12:
                    watermelon = Watermelon(x * tile_size, y * tile_size)
                    collectible_group.add(watermelon)
                    pass

                elif tile == -3:
                    #end
                    end = End(x * tile_size, y * tile_size)
                    end_group.add(end)
                    pass


    def draw(self):
        for tile in self.obstacle_list:

            tile[1][0] -= screen_scroll[0]
            tile[1][1] -= screen_scroll[1]

            screen.blit(tile[0], tile[1])

        tile[1][0] -= screen_scroll[0]
        tile[1][1] -= screen_scroll[1]

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('zombie1.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.height = self.image.get_height()
        self.width = self.image.get_width()
        self.baseSpeed = 2
        self.currentSpeed = self.baseSpeed
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.health = 100
        self.currentHealth = self.health
        self.health_bar_length = 45
        self.health_ratio = self.currentHealth / self.health_bar_length
        self.hitDamage = 20

        self.freezeTime = 0
        self.freezeMultiplier = 1
        self.freeze = 0
        # 0 = off, 1 = on but hasnt updated, 2 = updated

        self.burnTime = 0
        self.burnCountdown = fps * 2

    def attack(self):
        projectile = Projectile(self.rect.centerx + (0.8 * self.rect.size[0] * self.direction), self.rect.centery,
                                self.direction)
        projectile_group.add(projectile)

    def update(self):
        dx = 0
        dy = 0

        if self.freeze > 0:
            self.freezeUpdate()

        if self.currentHealth <= 0:
            self.kill()

        if self.burnTime > 0 and self.burnCountdown <= 0:
            self.burnCountdown = fps * 2
            self.currentHealth -= (0.15 * self.health)

        dx += (self.move_direction * self.currentSpeed) - screen_scroll[0]

        self.move_counter += 1

        if abs(self.move_counter) > 30 / self.freezeMultiplier:
            self.move_direction *= -1
            self.move_counter *= -1

        if self.currentHealth < self.health and player.enemyHealthDisplay == True:
            pygame.draw.rect(screen, (0, 255, 0), (
            self.rect.centerx - (0.5 * self.health_bar_length), self.rect.centery - (0.6 * self.height),
            self.currentHealth / self.health_ratio, 10))
            pygame.draw.rect(screen, (255, 255, 255), (
            self.rect.centerx - (0.5 * self.health_bar_length), self.rect.centery - (0.6 * self.height),
            self.health_bar_length, 10), 2)

        if self.burnCountdown > 0:
            self.burnCountdown -= 1

        if self.burnTime > 0:
            self.burnTime -= 1

        # scroll

        for tile in world.obstacle_list:
            # (x direction)
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                self.move_direction *= -1
        self.rect.x += dx

    def freezeUpdate(self):
        if self.freeze == 1:

            self.currentSpeed = self.currentSpeed * self.freezeMultiplier
            self.freeze = 2


        elif self.freeze == 2:
            if self.freezeTime == 0:
                self.freeze == 0

                self.currentSpeed = self.currentSpeed / self.freezeMultiplier
                self.freezeMultiplier = 1
            else:
                self.freezeTime -= 1

class End(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("tiles/-3.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (tile_size, tile_size))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        self.rect.x -= screen_scroll[0]
        self.rect.y -= screen_scroll[1]

    


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 5
        self.name = 'projectile'

        self.imagesize = [21, 10]
        self.direction = direction
        self.image = projectile_img
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.startX = x
        self.startY = y
        self.leftoverHits = 1

        self.cooldown = 50  # in milliseconds
        self.dmg = 15
        self.energyCost = 50
        self.range = 7

        self.hitEntities = set()
        self.ghost = False

        self.freeze = False
        self.freezeTime = 0
        self.freezeMultiplier = 1

        self.burnTime = 0

        self.disappear = False
        self.dAnimation = False
        self.dCounter = 0 #disappear animation counter for speed 
        self.dCooldown = 2 #disappear animation speed (higher = slower, lower = faster)
        self.dIndex = 1 #indexes which animation
        self.dImages = 0
        
        #same thing for dsiappear but hit animation
        self.hit = False
        self.hAnimation = False
        self.hCounter = 0
        self.hCooldown = 2 
        self.hIndex = 1
        self.hImages = 0

    def update(self):
        dx = (self.direction * self.speed) - screen_scroll[0]
        self.rect.x += dx


        
        if self.disappear == False and self.hit == False:
            key = pygame.key.get_pressed()
            if key[pygame.K_LCTRL] == True and key[pygame.K_b] == True:
                    pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)

            # check if bullet out of range
            if (self.direction == -1 and self.rect.left < self.startX - (self.range * tile_size) ) or (
                    self.direction == 1 and self.rect.right > self.startX + (self.range * tile_size)):
                self.disappear = True
                

            if self.ghost == False:
                for tile in world.obstacle_list:
                    if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.rect.width,
                                        self.rect.height):
                        dx = 0
                        screenshake = 30
                        self.hit = True



            for zomb in zombie_group:
                if zomb.rect.colliderect(self.rect):
                    if zomb not in self.hitEntities:
                        if self.leftoverHits == 1:
                            self.hit = True
                        else:
                            self.hitEntities.add(zomb)
                            self.leftoverHits -= 1

                        zomb.currentHealth -= self.dmg
                        if self.freeze == True:

                            if zomb.freeze == 2:
                                zomb.currentSpeed = zomb.currentSpeed / zomb.freezeMultiplier
                            zomb.freezeMultiplier = min(zomb.freezeMultiplier, self.freezeMultiplier)
                            zomb.freezeTime = max(self.freezeTime, zomb.freezeTime)
                            zomb.freeze = 1

                        zomb.burnTime = max(self.burnTime, zomb.burnTime)

        

        elif self.disappear == True and self.dAnimation == True: # there is a disappear animation and the bullet has died
            
            self.dCounter += 1
            
            self.speed = 0
            #disappear animation:

            if self.dCounter > self.dCooldown:
                self.dCounter = 0
                self.dIndex += 1
                if self.dIndex > self.dImages:
                    self.kill()
                else:
                    self.image = pygame.image.load(f'assets/spell_assets/{self.name}/{self.name}_d{self.dIndex}.png').convert_alpha()

        elif self.hit == True and self.hAnimation == True: # hit animation
            self.hCounter += 1
            self.speed = 0
            if self.hCounter > self.hCooldown:
                self.hCounter = 0
                self.hIndex += 1
                if self.hIndex > self.hImages:
                    self.kill()
                else:
                    self.image = pygame.image.load(f'assets/spell_assets/{self.name}/{self.name}_h{self.hIndex}.png').convert_alpha()
                    self.image = pygame.transform.scale(self.image, (max(self.imagesize[0],self.imagesize[1]), max(self.imagesize[0],self.imagesize[1])))

        else: #bullet has died but no disappear animation or hit
            self.kill()



class Fireball(Projectile):
    def __init__(self, x, y, direction):
        super().__init__(x, y, direction)
        self.dmg = round(np.clip(np.random.normal(loc=25, scale=2.3), 20, 30))
        self.name = 'fireball'
        self.imagesize = [40, 24]
       
        self.disappearAnimation = True
        self.cooldown = 50
        self.speed = 8
        self.range = 10
        burnRNG = np.random.randint(100)
       
        if burnRNG < 10:
            self.burnTime = 6 * fps
            # print('burned')

        self.dAnimation = True
        self.hAnimation = True
        self.dImages = 4
        self.hImages = 4

        self.energyCost = 60
        self.image = pygame.image.load('assets/spell_assets/fireball/fireball1.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (40, 24))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)


class Snowball(Projectile):
    def __init__(self, x, y, direction):
        super().__init__(x, y, direction)
        self.dmg = 20
        self.range = 8
        self.speed = 5
        self.energyCost = 60
        self.cooldown = 70
        self.image = pygame.image.load('assets/spell_assets/snowball.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)

        self.freeze = True
        self.freezeMultiplier = 0.5
        self.freezeTime = 5 * fps


class GhoulShot(Projectile):
    def __init__(self, x, y, direction):
        super().__init__(x, y, direction)
        self.dmg = 35
        self.range = 15
        self.speed = 12
        self.cooldown = 200
        self.ghost = True
        self.energyCost = 120
        self.leftoverHits = 3
        self.image = pygame.image.load('assets/spell_assets/ghouldash.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (35, 35))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)

class Watermelon(pygame.sprite.Sprite):
     def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/collectibles/watermelon.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (25, 25))
        self.rect = self.image.get_rect()
        self.rect.x = x + tile_size
        self.rect.y = y
        self.height = self.image.get_height()
        self.width = self.image.get_width()
    
     def update(self):
        key = pygame.key.get_pressed()

        #hitboxes
        if key[pygame.K_LCTRL] == True and key[pygame.K_b] == True:
                pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)
                
        if self.rect.colliderect(player.rect):
            if player.currentEnergy + 0.25 * player.baseEnergy > player.baseEnergy:
                player.currentEnergy = player.baseEnergy
            else:
                player.currentEnergy += 0.25 * player.baseEnergy
            self.kill()

        self.rect.x -= screen_scroll[0]


# empty tile list
world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)

# load in level data and create world
with open(f'levels/level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)


class Player():
    def __init__(self, x, y):

        self.baseEnergy = 1000
        self.currentEnergy = 1000
        self.energyuseMultiplier = 1
        self.energy_bar_length = 250
        self.energy_ratio = self.currentEnergy / self.energy_bar_length
        self.regenspeed = 10

        self.statWaitTime = 0

        # settings
        self.enemyHealthDisplay = True
        self.damageDisplay = False

        self.spells = [Projectile, Fireball, 2, Snowball, GhoulShot, 5]
        self.statSpells = {2: self.mend, 5: self.reserve}
        self.energyCosts = [50, 0, 60, 0, 200, 0, 100, 0, 120, 0, 300, 0]
        # ^ wait times included (for ex: energy cost for move 0 is energyCosts[0] and waitTime is energyCosts[1], energy for n: energyCosts[n*2], waiTime: energyCosts[2n + 1]
        self.projectileAmounts = [1, 1, 1, 1, 1, 1]
        self.multihitCooldown = 0
        self.spell1 = 4
        self.spell2 = 1
        self.spell3 = 2
        self.spell4 = 3

        self.freeze = False
        self.freezeTime = 0
        self.freezeMultiplier = 0
        self.burnTime = 0

        self.doubleJump = True

        self.attackCooldown1 = 0
        self.attackCooldown2 = 0
        self.attackCooldown3 = 0
        self.attackCooldown4 = 0
        self.statCooldown = 0

        self.totalCooldown1 = 0
        self.totalCooldown2 = 0
        self.totalCooldown3 = 0
        self.totalCooldown4 = 0

        self.baseHealth = 100
        self.currentHealth = 100
        self.health_bar_length = 250
        self.health_ratio = self.currentHealth / self.health_bar_length

        self.images_right = []
        self.jumpCooldown = True

        # statmove counters
        self.reserveCounter = 0

        self.images_left = []
        self.index = 0
        self.counter = 0
        self.energyCounter = 0

        for num in range(1, 5):
            img_right = pygame.image.load(f'guy1_{num}.png').convert_alpha()
            img_right = pygame.transform.scale(img_right, (30, 50))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.image = self.images_right[self.index]
        self.speed = 3
        self.sprintspeed = math.ceil(self.speed * 1.5)
        self.direction = 1
        self.gravity = 0.2

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False

    def rest(self):
        key = pygame.key.get_pressed()

        if ((key[pygame.K_LSHIFT] == False and key[pygame.K_RSHIFT] == False) or (key[pygame.K_d] == False and key[
            pygame.K_a] == False)) and self.currentEnergy < self.baseEnergy and self.vel_y == 0 and game_over == 0 and \
                key[pygame.K_1] == False:

            if self.baseEnergy - self.currentEnergy < 10:
                self.currentEnergy = self.baseEnergy
            else:
                self.currentEnergy += self.regenspeed

    def mend(self):

        if self.currentHealth + round(0.3 * self.baseHealth) > self.baseHealth:
            self.currentHealth = self.baseHealth
        else:
            self.currentHealth += round(0.3 * self.baseHealth)
        self.currentEnergy -= 300
        self.statCooldown = 2000

    def reserve(self):

        self.currentEnergy -= 300 * self.energyuseMultiplier
        self.reserveCounter = 500
        self.energyuseMultiplier = 0
        self.statCooldown = 1500


    def update(self, game_over, start_time, dt):

        walk_cooldown = 7
        screen_scroll[0] = 0
        dt= dt

        # change in x, y (deltaX, deltaY)
        dx = 0
        dy = 0
        key = pygame.key.get_pressed()
        if game_over == 0:
            # get key presses

            # hitboxes
            if key[pygame.K_LCTRL] == True and key[pygame.K_b] == True:
                pygame.draw.rect(screen, (255, 255, 255), self.rect, 2)
            # sprint/movement
            if key[pygame.K_a] and self.statWaitTime == 0:

                if (key[pygame.K_LSHIFT] == True or key[pygame.K_RSHIFT] == True) and self.currentEnergy >= 12:

                    dx -= self.sprintspeed
                    self.currentEnergy -= 3
                    self.counter += 1

                else:
                    dx -= self.speed

                self.counter += 1

                self.direction = -1

            if key[pygame.K_d] and self.statWaitTime == 0:
                if (key[pygame.K_LSHIFT] == True or key[pygame.K_RSHIFT] == True) and self.currentEnergy >= 12:


                    dx += self.sprintspeed
                    self.counter += 1

                    self.currentEnergy -= 3
                else:

                    dx += self.speed



                self.counter += 1
                self.direction = 1

            if key[pygame.K_1] == True and self.attackCooldown1 == 0:
                if self.energyCosts[self.spell1 * 2] * self.energyuseMultiplier <= self.currentEnergy:
                    if (type(self.spells[self.spell1]) == int):
                        self.statSpells[self.spell1]()
                        self.totalCooldown1 = self.statCooldown
                        self.attackCooldown1 = self.statCooldown
                    else:

                        projectile = self.spells[self.spell1](
                            self.rect.centerx, player.rect.centery,
                            self.direction)
                        projectile_group.add(projectile)
                        self.totalCooldown1 = projectile.cooldown
                        self.attackCooldown1 = projectile.cooldown
                        self.currentEnergy -= (projectile.energyCost * self.energyuseMultiplier)

            if key[pygame.K_2] == True and self.attackCooldown2 == 0:
                if self.energyCosts[self.spell2 * 2] * self.energyuseMultiplier <= self.currentEnergy:
                    if (type(self.spells[self.spell2]) == int):
                        self.statSpells[self.spell2]()
                        self.totalCooldown2 = self.statCooldown
                        self.attackCooldown2 = self.statCooldown
                    else:
                        projectile = self.spells[self.spell2](
                            self.rect.centerx, player.rect.centery,
                            self.direction)
                        projectile_group.add(projectile)
                        self.totalCooldown2 = projectile.cooldown
                        self.attackCooldown2 = projectile.cooldown
                        self.currentEnergy -= (projectile.energyCost * self.energyuseMultiplier)

            if key[pygame.K_3] == True and self.attackCooldown3 == 0:
                if self.energyCosts[self.spell3 * 2] * self.energyuseMultiplier <= self.currentEnergy:

                    if (type(self.spells[self.spell3]) == int):
                        self.statSpells[self.spell3]()
                        self.totalCooldown3 = self.statCooldown
                        self.attackCooldown3 = self.statCooldown
                    else:
                        projectile = self.spells[self.spell3](
                            self.rect.centerx, player.rect.centery,
                            self.direction)
                        projectile_group.add(projectile)
                        self.totalCooldown3 = projectile.cooldown
                        self.attackCooldown3 = projectile.cooldown
                        self.currentEnergy -= (projectile.energyCost * self.energyuseMultiplier)

            if key[pygame.K_4] == True and self.attackCooldown4 == 0:
                if self.energyCosts[self.spell4 * 2] * self.energyuseMultiplier <= self.currentEnergy:
                    if (type(self.spells[self.spell4]) == int):
                        self.statSpells[self.spell4]()
                        self.totalCooldown4 = self.statCooldown
                        self.attackCooldown4 = self.statCooldown


                    else:
                        for i in range(0, self.projectileAmounts[self.spell4]):
                            projectile = self.spells[self.spell4](
                                self.rect.centerx, self.rect.centery - 5,
                                self.direction)
                            projectile_group.add(projectile)
                        self.totalCooldown4 = projectile.cooldown
                        self.attackCooldown4 = projectile.cooldown
                        self.currentEnergy -= (projectile.energyCost * self.energyuseMultiplier)

            if key[pygame.K_SPACE] and self.jumped == False and self.jumpCooldown == True and self.statWaitTime == 0:
                self.vel_y = -5
                self.jumped = True
                self.jumpCooldown = False

            elif key[pygame.K_SPACE] and self.doubleJump == True and self.jumped == False and self.jumpCooldown == False and self.currentEnergy >= 200 and self.statWaitTime == 0:
                self.vel_y = -7
                self.jumped = True
                self.jumpCooldown = False
                self.currentEnergy -= 200
            if key[pygame.K_SPACE] == False:
                self.jumped = False
            if key[pygame.K_a] == False and key[pygame.K_d] == False and self.statWaitTime == 0:
                self.counter = 0
                self.index = 0

                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # animation

            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # add gravity
            self.vel_y += self.gravity
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y



            # check for collision
            for tile in world.obstacle_list:
                # (x direction)
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # check for collision (y direction)
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # check if below ground (jumping)
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # falling
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.jumpCooldown = True

            # collision w/ enemies

            for enemy in zombie_group:
                if enemy.rect.colliderect(self.rect):
                    if pygame.time.get_ticks() - start_time > 300:
                        self.currentHealth -= enemy.hitDamage
                        if self.currentHealth <= 0:
                            game_over = -1
                        start_time = pygame.time.get_ticks()

            for end in end_group:
                if end.rect.colliderect(self.rect):
                    game_over = 1

            self.rect.x += dx
            self.rect.y += dy 

        # draw player onto screen
        if (self.attackCooldown1 > 0):
            self.attackCooldown1 -= 1

        if (self.attackCooldown2 > 0):
            self.attackCooldown2 -= 1

        if (self.attackCooldown3 > 0):
            self.attackCooldown3 -= 1

        if (self.attackCooldown4 > 0):
            self.attackCooldown4 -= 1

        screen.blit(self.image, self.rect)

        if self.reserveCounter > 0:
            self.reserveCounter -= 1

            if self.reserveCounter == 0:
                self.energyuseMultiplier = 1

        self.energyUpdate()
        self.moveReload()
        return (game_over, start_time, dx, dy)

    def energyUpdate(self):
        pygame.draw.rect(screen, (254, 1, 154), (22, 11, self.currentEnergy / self.energy_ratio, 20))
        pygame.draw.rect(screen, (255, 255, 255), (22, 11, self.energy_bar_length, 20), 2)
        pygame.draw.rect(screen, (0, 255, 0), (22, 37, self.currentHealth / self.health_ratio, 20))
        pygame.draw.rect(screen, (255, 255, 255), (22, 37, self.energy_bar_length, 20), 2)


    def moveReload(self):
        #reload bars
        # move 1 
        if (self.attackCooldown1 != 0):
            pygame.draw.rect(screen, (254, 1, 154), (20, 128, (self.totalCooldown1 - self.attackCooldown1) * (52 / self.totalCooldown1), 15))
            pygame.draw.rect(screen, (255, 255, 255), (20, 128, 52, 15), 2)
        # move 2
        if (self.attackCooldown2 != 0):
            pygame.draw.rect(screen, (254, 1, 154), (80, 128, (self.totalCooldown2 - self.attackCooldown2) * (52 / self.totalCooldown2), 15))
            pygame.draw.rect(screen, (255, 255, 255), (80, 128, 52, 15), 2)
        # move 3
        if (self.attackCooldown3 != 0):
            pygame.draw.rect(screen, (254, 1, 154), (140, 128, (self.totalCooldown3 - self.attackCooldown3) * (52 / self.totalCooldown3), 15))
            pygame.draw.rect(screen, (255, 255, 255), (140, 128, 52, 15), 2)
        # move 4
        if (self.attackCooldown4 != 0):
            pygame.draw.rect(screen, (254, 1, 154), (200, 128, (self.totalCooldown4 - self.attackCooldown4) * (52 / self.totalCooldown4), 15))
            pygame.draw.rect(screen, (255, 255, 255), (200, 128, 52, 15), 2)



zombie_group = pygame.sprite.Group()
collectible_group = pygame.sprite.Group()
projectile_group = pygame.sprite.Group()
end_group = pygame.sprite.Group()
dead_group = pygame.sprite.Group()





world = World()
world.process_data(world_data)


player = Player(spawn[0], spawn[1])


run = True

energyCooldown = 0


async def main():
    global run
    global game_over
    global screenshake
    global bg_scroll
    global start_time
    global world
    global fadeCounter
    global energyCooldown
    while run:
        #your main game loop       
        clock.tick(fps)
        if game_over == 0:
            levelcooldown = True
            dt = clock.tick()

            

            player_tuple = player.update(game_over, start_time, dt)
            game_over = player_tuple[0]
            start_time = player_tuple[1]
            dx = player_tuple[2]
            dy = player_tuple[3]

            screen_scroll[0] = math.floor((player.rect.x - screen_scroll[0] - 380)/20)
            player.rect.x -= screen_scroll[0]
            levelProgress[0] += screen_scroll[0]

            for proj in projectile_group:
                proj.startX -= screen_scroll[0]



            draw_bg()
            world.draw()
            

            dead_group.update()
            end_group.update()
            zombie_group.update()
            projectile_group.update()
            collectible_group.update()
            
            bg_scroll += screen_scroll[0]
        
            player.update(game_over, start_time, dt)
            end_group.draw(screen)
            projectile_group.draw(screen)
            collectible_group.draw(screen)
            zombie_group.draw(screen) 
            dead_group.draw(screen)
            
            

            screen.blit(energy_img, (250, 2))
            screen.blit(health_img, (5, 25))

            screen.blit(spell_slot, (20, 70))
            screen.blit(spell_slot, (80, 70))
            screen.blit(spell_slot, (140, 70))
            screen.blit(spell_slot, (200, 70))

            #fade in
            
            if fadeCounter > 0:
                fadeCounter -= 8
                if fadeCounter < 0:
                    fadeCounter = 0
                
                pygame.draw.rect(screen, BLACK, (0, 0, screen_width, fadeCounter))
                pygame.draw.rect(screen, BLACK, (0, (screen_height / 2) + ((screen_height / 2) - fadeCounter), screen_width, screen_height / 2))
                

            

            energyCooldown += dt

            if energyCooldown > 10:
                player.rest()
                energyCooldown = 0

            if screenshake > 0:
                screenshake -= 1

            render_offset = [0, 0]
            if screenshake:
                render_offset[0] = random.randint(0, 8) - 4
                render_offset[1] = random.randint(0, 8) - 4

            
            
        else: 
        

            
            
            bg_scroll += screen_scroll[0]
            player.update(game_over, start_time, dt)
            end_group.draw(screen)
            projectile_group.draw(screen)
            collectible_group.draw(screen)
            zombie_group.draw(screen) 
            dead_group.draw(screen)
            

            
            

            screen.blit(energy_img, (250, 2))
            screen.blit(health_img, (5, 25))
            
            screen.blit(spell_slot, (20, 70))
            screen.blit(spell_slot, (80, 70))
            screen.blit(spell_slot, (140, 70))
            screen.blit(spell_slot, (200, 70))

            if fadeCounter < fadeAm:
                fadeCounter += 5
                if fadeCounter >= fadeAm:
                    fadeCounter = fadeAm
                    if game_over == 1 and levelcooldown == True:
                        
                        level += 1
                        levelcooldown = False

                        if level <= TOTAL_LEVELS:
                            world_data = []
                            world = reset_level(level)
                            game_over = 0
                            fadeCounter = screen_height / 2
                            player.rect.x = spawn[0]
                            player.rect.y = spawn[1]

                        
                
            pygame.draw.rect(screen, BLACK, (0, 0, screen_width, fadeCounter))
            pygame.draw.rect(screen, BLACK, (0, screen_height - fadeCounter, screen_width, fadeAm) )


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        
        pygame.display.update()
    
        await asyncio.sleep(0)
        if not run:
            pygame.quit()
            return

asyncio.run(main())
