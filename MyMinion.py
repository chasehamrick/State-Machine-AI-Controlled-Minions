'''
 * Copyright (c) 2014, 2015 Entertainment Intelligence Lab, Georgia Institute of Technology.
 * Originally developed by Mark Riedl.
 * Last edited by Mark Riedl 05/2015
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
'''

import sys, pygame, math, numpy, random, time, copy
from pygame.locals import * 

from constants import *
from utils import *
from core import *
from moba import *

MINIONRANGE = 250
DODGERANGE = 250
numberProtect = 0
PROTECTCOUNTER = 150
DODGECOUNTER = 5

class MyMinion(Minion):
    
    def __init__(self, position, orientation, world, image = NPC, speed = SPEED, viewangle = 360, hitpoints = HITPOINTS, firerate = FIRERATE, bulletclass = SmallBullet):
        Minion.__init__(self, position, orientation, world, image, speed, viewangle, hitpoints, firerate, bulletclass)
        self.states = [Idle]
        ### Add your states to self.states (but don't remove Idle)
        ### YOUR CODE GOES BELOW HERE ###
        self.states += [Move, AttackBase, AttackTower, ProtectBase, Dodge]

        ### YOUR CODE GOES ABOVE HERE ###

    def start(self):
        Minion.start(self)
        self.changeState(Idle)





############################
### Idle
###
### This is the default state of MyMinion. The main purpose of the Idle state is to figure out what state to change to and do that immediately.

class Idle(State):
    
    def enter(self, oldstate):
        State.enter(self, oldstate)
        # stop moving
        self.agent.stopMoving()
    
    def execute(self, delta = 0):
        State.execute(self, delta)
        ### YOUR CODE GOES BELOW HERE ###

        self.agent.changeState(Move)

        ### YOUR CODE GOES ABOVE HERE ###
        return None

##############################
### Taunt
###
### This is a state given as an example of how to pass arbitrary parameters into a State.
### To taunt someome, Agent.changeState(Taunt, enemyagent)

class Taunt(State):

    def parseArgs(self, args):
        self.victim = args[0]

    def execute(self, delta = 0):
        if self.victim is not None:
            print "Hey " + str(self.victim) + ", I don't like you!"
        self.agent.changeState(Idle)

##############################
### YOUR STATES GO HERE:



class Move(State):
    
    def enter(self, delta = 0):
        global numberProtect

        if (numberProtect < 4):
            print "defend"
        else:
            minionTeam = self.agent.getTeam()
            playerBase = self.agent.world.getEnemyBases(minionTeam)
            playerTowers = self.agent.world.getEnemyTowers(minionTeam)
            if (len(playerTowers) > 0):
                self.agent.navigateTo(closestDestination(self.agent, playerTowers)[0].getLocation())
            elif (len(playerBase) > 0):
                self.agent.navigateTo(closestDestination(self.agent, playerBase)[0].getLocation())
    
    def execute(self, delta):
        global numberProtect

        if (numberProtect < 4):
            numberProtect += 1
            self.agent.changeState(ProtectBase, None, PROTECTCOUNTER)
        else:
            minionTeam = self.agent.getTeam()
            currentPos = self.agent.getLocation()
            playerBase = self.agent.world.getEnemyBases(minionTeam)
            playerTowers = self.agent.world.getEnemyTowers(minionTeam)
        
            if (not self.agent.isMoving()):
                if (len(playerTowers) > 0):
                    self.agent.navigateTo(closestDestination(self.agent, playerTowers)[0].getLocation())
                elif (len(playerBase) > 0):
                    self.agent.navigateTo(closestDestination(self.agent, playerBase)[0].getLocation())
        
            if (len(playerBase) > 0 and len(playerTowers) == 0 and distance(self.agent.getLocation(), playerBase[0].getLocation()) < 150):
                self.agent.changeState(AttackBase)
        
            if (len(playerTowers) > 0 and closestDestination(self.agent, playerTowers)[1] < 150):
                self.agent.changeState(AttackTower)


class AttackBase(State):
    
    def enter(self, oldstate):
        self.agent.stop()
        
    def execute(self, delta = 0):
        minionTeam = self.agent.getTeam()
        playerBase = self.agent.world.getEnemyBases(minionTeam)
        if (len(playerBase) > 0):
            shootEnemy(self.agent, playerBase[0])
        else:
            self.agent.changeState(Move)

class AttackTower(State):

    def enter(self, oldstate):
        self.agent.stop()
        minionTeam = self.agent.getTeam()
        playerTowers = self.agent.world.getEnemyTowers(minionTeam)
        self.target = closestDestination(self.agent, playerTowers)[0]
        
    def execute(self, delta = 0):
        minionTeam = self.agent.getTeam()
        playerTowers = self.agent.world.getEnemyTowers(minionTeam)
        if (len(playerTowers) > 0):
            shootEnemy(self.agent, self.target)
            if (not self.target.isAlive()):
                self.agent.changeState(Move)
            else:
                self.agent.changeState(Move)
            
class ProtectBase(State):
    
    def parseArgs(self, args):
        self.dest = args[0]
        self.counter = args[1]
        self.bestDestinations = None

    def enter(self, oldstate):
        myTowers = self.agent.world.getTowersForTeam(self.agent.getTeam())
        myBase = self.agent.world.getBaseForTeam(self.agent.getTeam())

        if self.dest == None or self.counter == 0:

            self.counter = PROTECTCOUNTER
            targetLocation = myBase.getLocation()
            possDest = self.agent.getPossibleDestinations()
            possDest = [d for d in possDest if (distance(d, targetLocation) < MINIONRANGE and distance(d, targetLocation) > (MINIONRANGE - 150))]

            rankDest = []
            for i, nextPos in enumerate(possDest):
                towerWeight = sum([-1.0*0.5*distance(nextPos, t.getLocation()) for t in myTowers])
                baseWeight = -1.0*0.5*distance(nextPos, myBase.getLocation())

                rankDest.append((i, towerWeight + baseWeight))

            rankDest = sorted(rankDest, key=lambda x: x[1], reverse = True)

            self.bestDestinations = [possDest[rankDest[i][0]] for i in range(5)]

            self.dest = random.choice(self.bestDestinations)

        self.agent.navigateTo(self.dest)

    def execute(self, delta = 0):
        
        inRangeBullets = bulletsInRange(self.agent)
        playerAgents = self.agent.world.getEnemyNPCs(self.agent.getTeam())
        playerAgents = [p for p in playerAgents if inShootingRange(self.agent, p, MINIONRANGE)]

        if (len(playerAgents) > 0):
            closestTarget = getClosest(playerAgents, self.agent.getLocation())
            self.agent.turnToFace(closestTarget.getLocation())
            self.agent.shoot()

        if (len(inRangeBullets) > 0):
            bullet = getClosest(inRangeBullets, self.agent.getLocation())
            self.agent.changeState(Dodge, DODGECOUNTER, None)

        else:
            self.agent.changeState(ProtectBase, self.dest, self.counter - 1)

class Dodge(State):
        
    def parseArgs(self, args):
        self.counter = args[0]
        self.dest = args[1]
        
    def enter(self, oldstate):
        base = self.agent.world.getBaseForTeam(self.agent.getTeam())
        
        if self.counter == None:
            possibleDest = self.agent.getPossibleDestinations()
            
            if base != None:
                possibleDest = [d for d in possibleDest if (distance(self.agent.getLocation(), d) < 50 and distance(d, base.getLocation()) < 100)]
            else:
                possibleDest = [d for d in possibleDest if (distance(self.agent.getLocation(), d) <50)]
            
            self.dest = random.choice(possibleDest)
            self.agent.navigateTo(self.dest)
    
    def execute(self, delta = 0):
    
        if (self.counter == 0):
            self.agent.changeState(ProtectBase, self.dest, PROTECTCOUNTER)
        
        else:
            self.agent.changeState(Dodge, self.counter - 1, self.dest)
            
def closestDestination(agent, dest):
    currentPos = agent.getLocation()
    destLocations = []
    for d in dest:
        destLocations.append(d.getLocation())
    distToDestLoc = map(distance, [currentPos for i in range(len(destLocations))], destLocations)
    target = dest[distToDestLoc.index(min(distToDestLoc))]
    targetDist = distToDestLoc[distToDestLoc.index(min(distToDestLoc))]
    return target, targetDist

def shootEnemy(agent, target):
    enemyPos = target.getLocation()
    agent.turnToFace(enemyPos)
    agent.shoot()
    
def getClosestDistances(list, currPos):
    dist = []
    for l in list:
        dist.append( (l, distance( currPos, l )) )
    dist.sort(key = lambda x:x[1])

    return dist[0][0]

def getClosest(list, currPos):

    if list == None or currPos == None or len(list) == 0:
        return None

    else:
        dist = []
        for l in list:
            dist.append( (l, distance( currPos, l.getLocation() )) )
        dist.sort(key = lambda x:x[1])

        return dist[0][0]
        
def bulletsInRange(agent):
    world = agent.world
    allBullets = world.getBullets()
    inRangeBullets = []
    
    for b in allBullets:
        if ((b.getOwner().getTeam() != agent.getTeam()) and (distance(b.getLocation(), agent.getLocation()) < DODGERANGE)):
            inRangeBullets.append(b)
    
    return inRangeBullets

def inShootingRange(agent, target, range):
    visible = agent.getVisible()
    if((target in visible) and (distance(target.getLocation(), agent.getLocation()) < range)):
        return True
    return False