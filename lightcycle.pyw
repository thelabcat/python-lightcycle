#!/usr/bin/env python3
#Lightcycle v2.9
#S.D.G.

#Modules
import pygame, time, sys, os
from pygame.locals import *
from pygame.color import THECOLORS

pygame.init() #Start pygame systems

#Script path, so can be run from anywhere. This "if" statement may be unneccesary.
if not sys.path[0]:
    PATH=sys.path[1]+os.sep
else:
    PATH=sys.path[0]+os.sep


#/-- U S E R  S E T T I N G S --\
#Grid dimensions (in terms of 4-ways which the bikes can operate on)
GRID_WIDTH=30
GRID_HEIGHT=30

GRID_PIX_SIZE=20 #One cell's edge length (cells are always square)
BIKE_PIX_SPEED=5 #Bike speed on screen in pixels (per single frame). To find cells per second, divide GRID_PIX_SIZE by this and multiply by FPS.

BACKGROUND_COLOR=(0, 0, 0, 255) #Game background color
LARGE_FONT=pygame.font.Font("freesansbold.ttf", 60) #Large font
SMALL_FONT=pygame.font.Font("freesansbold.ttf", 30) #Small font

WALL_WIDTH=8 #Width of wall trail left behind by each bike
TURN_RADIUS=int(WALL_WIDTH/2) #Radius of cirlces drawn at turns

#Bike dimensions (drawing code is in Game object)
BIKE_RADIUS=13
BIKE_RIM=2

GRID_COLOR=THECOLORS["lightgrey"] #Color of grid lines
BIKE_RIM_COLOR=THECOLORS["darkgrey"] #Color of bikes' rims

START_KEY=K_SPACE #"Press this to start."
MODECHANGE_KEY=K_RSHIFT #Key to change modes

DECLARE_DELAY=2.75 #Time to wait after game end before declaring winner.
COUNTDOWN_TIME=3 #Time in seconds between pressing the start key and the bikes start moving.

FPS=50 #Game FPS
#\------------------------------/


DISP_SIZE=((GRID_WIDTH+1)*GRID_PIX_SIZE, (GRID_HEIGHT+1)*GRID_PIX_SIZE) #Display size, based on grid size

VELOCITIES=((0, -1), (0, 1), (1, 0), (-1, 0)) #Possible bike velocities in arrow key order
OPPOSING=(1, 0, 3, 2) #In the order of their matching velocities, the indexes of the velocities' opposites.

RATING_RES=100 #How much to magnify move ratings before integer-ing. Note: This may no longer be neccesary

MODES=3 #Number of modes, used in mode selection code

#Bike stati
ALIVE="alive"
CRASHED="crashed"
TIED="tied"

#Settings for gold bike
GOLD_BIKE_KEYS=(K_w, K_s, K_d, K_a)
GOLD_BIKE_STARTPOS=[0, int(GRID_HEIGHT/2+0.5)-1]
GOLD_BIKE_FACING=2
GOLD_COLOR=THECOLORS["gold"]
GOLD_WALL="GW"

#Settings for blue bike
BLUE_BIKE_KEYS=(K_UP, K_DOWN, K_RIGHT, K_LEFT)
BLUE_BIKE_STARTPOS=[GRID_WIDTH-1, int(GRID_HEIGHT/2+0.5)-1]
BLUE_BIKE_FACING=3
BLUE_COLOR=THECOLORS["skyblue"]
BLUE_WALL="BW"

TIE_COLOR=((GOLD_COLOR[0]+BLUE_COLOR[0])/2, (GOLD_COLOR[1]+BLUE_COLOR[1])/2, (GOLD_COLOR[2]+BLUE_COLOR[2])/2) #Color of tie text and related graphics

#Texts for varous occasions
TITLE_TEXT=LARGE_FONT.render("LIGHTCYCLE", False, THECOLORS["black"], THECOLORS["white"])
PRESS_START_TEXT=LARGE_FONT.render("Press "+pygame.key.name(START_KEY)+" to start.", False, THECOLORS["white"])

PVP_TEXT=SMALL_FONT.render("Player vs. Player", False, THECOLORS["black"], THECOLORS["green"])
PVC1_TEXT=SMALL_FONT.render("Player (gold) vs. Computer (blue)", False, THECOLORS["black"], THECOLORS["green"])
PVC2_TEXT=SMALL_FONT.render("Computer (gold) vs. Player (blue)", False, THECOLORS["black"], THECOLORS["green"])
MODE_TEXTS=(PVP_TEXT, PVC1_TEXT, PVC2_TEXT) #Assembled list of mode texts as they are indexed by Game.mode

MODECHANGE_TEXT=SMALL_FONT.render("Press "+pygame.key.name(MODECHANGE_KEY)+" to change modes", False, THECOLORS["black"], THECOLORS["yellow"])

GOLD_WON_TEXT=LARGE_FONT.render("Gold won!", False, THECOLORS["black"], GOLD_COLOR)
BLUE_WON_TEXT=LARGE_FONT.render("Blue won!", False, THECOLORS["black"], BLUE_COLOR)
TIE_TEXT=LARGE_FONT.render("It's a Tie!", False, THECOLORS["black"], TIE_COLOR)
WINNER_TEXTS={GOLD_WALL:GOLD_WON_TEXT, BLUE_WALL:BLUE_WON_TEXT, TIED:TIE_TEXT} #Assembled dictionary of winner texts keyed by matching winning status

#Text positions
TITLE_TEXT_POS=(DISP_SIZE[0]/2-TITLE_TEXT.get_width()/2, DISP_SIZE[1]/4)
START_TEXT_POS=(DISP_SIZE[0]/2-PRESS_START_TEXT.get_width()/2, DISP_SIZE[1]*0.6)
MODECHANGE_TEXT_POS=(DISP_SIZE[0]/2-MODECHANGE_TEXT.get_width()/2, DISP_SIZE[1]*0.5)
mt_poss=[]
for mt in MODE_TEXTS:
    mt_poss.append((DISP_SIZE[0]/2-mt.get_width()/2, DISP_SIZE[1]*0.4))

MODE_TEXTS_POSS=mt_poss[:]
#Other text positions are calculated using center_text method and are not listed here


#Load sound files
SOUND_FILES={"start":"bikes start.wav", "running":"bikes running.wav", "death":"bike death.wav", "turn":"bike turn.wav"}
THEME_FILE="TRON repeatable 1.wav"
sounds={}

class DummySound(object):
    """Dummy sound object to use if files cannot be found"""
    def __init__(self, filename):
        self.fn=filename
    def play(self, *args, **kwargs):
        """Dummy sound playback, prints debug info"""
        print(self.fn, "dummy play,\a", *args, **kwargs)
        
    def stop(self, *args, **kwargs):
        """Dummy sound playback stop, prints debug info"""
        print(self.fn, "dummy stop,\a", *args, **kwargs)

for sn in SOUND_FILES:
    try:
        sounds[sn]=pygame.mixer.Sound(PATH+SOUND_FILES[sn])
    except FileNotFoundError:
        print(PATH+SOUND_FILES[sn], "not found. Using dummy.")
        sounds[sn]=DummySound(PATH+SOUND_FILES[sn])

try:
    pygame.mixer.music.load(PATH+THEME_FILE)
    MUSIC_LOADED=True
except pygame.error:
    print(PATH+THEME_FILE, "not found. Disabling theme music.")
    MUSIC_LOADED=False

#Set up display
ICON_FILE="lightcycle_icon.png"

DISPLAY=pygame.display.set_mode(DISP_SIZE)
pygame.display.set_caption("Lightcycle")

try:
    pygame.display.set_icon(pygame.image.load(PATH+ICON_FILE))
except FileNotFoundError:
    print(PATH+ICON_FILE, "not found. Going without icon.")
    
pygame.display.toggle_fullscreen()
pygame.mouse.set_visible(False)


fps_clock=pygame.time.Clock() #Create FPS clock


class Bike(object):
    def __init__(self):
        """Abstract Bike class with common methods"""
        raise NotImplementedError("this is an abstract object.")

    def setup(self, startpos, facing, wall):
        """Method for derived class to call and setup common attributes"""
        self.pos=startpos[:] #Initialize position
        self.oldpos=self.pos[:] #Initialize past position
        self.facing=facing #Initialize facing direction
        self.wall=wall #Set our wall string (never changes, absolute?)
        self.pixturns=[self.pixpos] #Log of turns in pixel coordinates for track drawer. Starts with our first position
    
    def pass_stuff(self, game, other_bike):
        """Method for Game to call and pass itself along with the other bike"""
        self.game=game
        self.other_bike=other_bike

    def move(self):
        """Move if we are not dead, otherwise return without moving"""
        if self.status!=ALIVE:
            return

        self.oldpos=self.pos[:] #Mark our old position

        #Move forward
        self.pos=self.add_vecs(self.pos, VELOCITIES[self.facing])

        self.game.board[self.oldpos[0]][self.oldpos[1]]=self.wall #Place a wall behind us

    def add_vecs(self, p1, p2):
        """Add a pair of 2 dimensional vectors and return in list format"""
        return [p1[0]+p2[0], p1[1]+p2[1]]

    def check_status(self, pos=None, otbpos=None, board=None):
        """Check the status of a bike at pos, with the other boke at otbpos and board as the game board (wall map). All default to their real values for this bike"""

        #Default to actual values if arguments not passed
        if not pos:
            pos=self.pos
        if not otbpos:
            otbpos=self.other_bike.pos
        if not board:
            board=self.game.board
            
        if pos[0]<0 or pos[0]>GRID_WIDTH-1: #Death if we pass out of grid's x bounds
            return CRASHED
        if pos[1]<0 or pos[1]>GRID_HEIGHT-1: #Death if we pass out of grid's y bounds
            return CRASHED
        if board[pos[0]][pos[1]][:] in (GOLD_WALL, BLUE_WALL): #Death if we hit a wall
            return CRASHED
        if pos==otbpos: #Tie death if the bikes collide
            return TIED

        return ALIVE
    
    @property
    def pixpos(self):
        """The position of the bike in screen pixels"""
        return ((self.pos[0]+1)*GRID_PIX_SIZE, (self.pos[1]+1)*GRID_PIX_SIZE)
    
    @property
    def oldpixpos(self):
        """The last position of the bike in screen pixels"""
        return ((self.oldpos[0]+1)*GRID_PIX_SIZE, (self.oldpos[1]+1)*GRID_PIX_SIZE)

    @property
    def status(self):
        """Convenience property: calls self.check_status()"""
        return self.check_status()

class PlayerBike(Bike):
    def __init__(self, keys, startpos, facing, wall):
        """Bike controlled by player. Control keys, starting position, facing direction, and wall string."""
        self.keys=keys #Our control keys
        self.setup(startpos, facing, wall) #Initialize our start position, facing direction, and wall string.
        
    def step(self, events):
        """Step the bike forward. Includes check for death. Pass list of pygame events."""
        new_command=self.facing*1 #Mark our original direction as the new command, so the last keypress in the event list will replace it, or it will be left as is
        for e in events: #Go through event list
            if e.type==KEYDOWN and e.key in self.keys: #If a control key for this bike was pressed...
                new_command=self.keys.index(e.key) #Find our facing direction by indexing our keyset as it is in the same order as velocities is.
                
        if new_command!=self.facing and new_command!=OPPOSING[self.facing]: #If we aren't already going this direction and we wouldn't be making a U-turn...
            self.facing=new_command #Change our facing direction
            sounds["turn"].play() #Play sound
            self.pixturns.append(self.pixpos) #Log the turn

        self.move() #Move forward one step on the board (does nothing if the bike is dead)
        
class ComputerBike(Bike):
    def __init__(self, startpos, facing, wall):
        """Bike controlled by algorithm. Starting position, facing direction, and wall string."""
        self.setup(startpos, facing, wall) #Initialize our start position, facing direction, and wall string.
    def step(self, events):
        """Step the bike forward. Includes check for death. Pass list of pygame events."""

        #Setup list of possible directions from here (including straight forward)
        possible=list(VELOCITIES)
        possible.pop(OPPOSING[self.facing]) #We can't make a U-turn

        ratings=[] #List of ratings for each direction
        for pv in possible: #For each possible direction...
            virt_pos=self.pos.copy() #Create a virtual version of this bike to wind forward time
            virt_otbpos=self.other_bike.pos.copy() #Create a virtual other bike to wind forward time
            virt_board=[] #Create a virtual board to wind forward time
            for gbr in self.game.board: #Coby the game board, row by row (neccesary because we need a shallow copy).
                virt_board.append(gbr[:])
            
            step_count=1 #Marker for the distance this move has been projected forward.
            while self.check_status(virt_pos, virt_otbpos, virt_board)==ALIVE and self.check_status(virt_otbpos, virt_pos, virt_board)==ALIVE: #Continue checking this move until someone dies
                virt_board[virt_pos[0]][virt_pos[1]]=self.wall #Mark a wall behind virtual us
                virt_board[virt_otbpos[0]][virt_otbpos[1]]=self.other_bike.wall #Mark a wall behind virtual other bike
                virt_pos=self.add_vecs(virt_pos, pv) #Move virtual us forward
                virt_otbpos=self.add_vecs(virt_otbpos, VELOCITIES[self.other_bike.facing]) #Move virtual other bike forward
                step_count+=1 #Increase marker for projection diatance

            #Rate each move based on how close an effect will happen. 2*RATING_RES is best, 0 is worst.
            if self.check_status(virt_pos, virt_otbpos, virt_board)!=ALIVE: #We died, so give negative rating
                ratings.append(int(RATING_RES-RATING_RES/step_count+0.5))
            elif self.check_status(virt_otbpos, virt_pos, virt_board)!=ALIVE: #Other bike died, so give positive rating
                ratings.append(int(RATING_RES+RATING_RES/step_count+0.5))
            else:
                ratings.append(RATING_RES) #Both bikes died (a tie), so give a neutral rating

        rating_total=ratings[0]+ratings[1]+ratings[2] #Sum the ratings of all three moves (DANGER: Very dependent on there being three and only three directions)
        
        facing=VELOCITIES.index(possible[ratings.index(max(ratings))]) #Pick first direction of those that have the highest rating

        #Check if we have changed direction based on above, and if so do turn stuff
        if self.facing!=facing:
            self.facing=facing #Update facing
            sounds["turn"].play() #Play sound
            self.pixturns.append(self.pixpos) #Log the turn
            
        self.move() #Move one step forward

class Game(object):
    def __init__(self):
        """Repeating game with start screen."""
        self.mode=0 #Our current mode. 0 is PvP, 1 is gold P vs blue C, 2 is blue P vs gold C
        while True: #Continue creating rounds forever
            self.wait_for_start() #Show the title screen, waiting for start key, including mode switching option

            #Bike selection from self.mode
            if self.mode in (0, 1): #If mode is either PvP or gold P...
                self.gold_bike=PlayerBike(GOLD_BIKE_KEYS, GOLD_BIKE_STARTPOS, GOLD_BIKE_FACING, GOLD_WALL) #Create new player gold bike
            if self.mode in (0, 2): #If mode is either PvP or blue P...
                self.blue_bike=PlayerBike(BLUE_BIKE_KEYS, BLUE_BIKE_STARTPOS, BLUE_BIKE_FACING, BLUE_WALL) #Create new player blue bike

            if self.mode==1: #If mode is blue C
                self.blue_bike=ComputerBike(BLUE_BIKE_STARTPOS, BLUE_BIKE_FACING, BLUE_WALL) #Create new computer blue bike
            elif self.mode==2: #If mode is gold C
                self.gold_bike=ComputerBike(GOLD_BIKE_STARTPOS, GOLD_BIKE_FACING, GOLD_WALL) #Create new computer gold bike
                
            #Create board (map of what is walled and what is not)
            self.board=[]
            for i in range(GRID_WIDTH):
                self.board.append([" "]*GRID_HEIGHT)
                
            self.game_running=True #Control variable for game loop

            #Pass self and the other bike to each bike
            self.gold_bike.pass_stuff(self, self.blue_bike)
            self.blue_bike.pass_stuff(self, self.gold_bike)
            
            self.mainloop() #Start game loop
        
    def mainloop(self):
        """Game mainloop"""
        sounds["start"].play() #Gentlemen, start your engine sounds!
        self.countdown_to_start() #Countdown to start

        sounds["running"].play(-1) #Start bikes running sound
        
        #Actual loop
        while self.game_running:
            events=pygame.event.get() #Get pygame events
            self.process_events(events) #Process events applicable to the Game object (currently only e.type==QUIT)
            self.gold_bike.step(events) #Step gold bike, handing events
            self.blue_bike.step(events) #Step blue bike, handing events
            
            if self.check_winner(): #Check for a win or tie
                self.game_running=False #Stop the game loop

            self.draw_out_step() #Draw out step.
        
        sounds["death"].play() #Play bike death sound
        sounds["running"].stop() #Stop bike running sound
        time.sleep(DECLARE_DELAY) #Wait a bit before declaring the winner
        pygame.event.get() #Clear pygame events so we don't accidentally skip the winner declaration
        self.declare_winner() #Once the game ends, declare a winner
    
    def wait_for_start(self):
        """Show game start screen and wait for start key"""
        if MUSIC_LOADED: #Start theme music if it loaded properly
            pygame.mixer.music.play(-1)

        #Loop for mode switching until start key is pressed
        waiting=True
        while waiting:
            self.draw_start_screen() #Draw start screen text and such
            events=pygame.event.get() #Get pygame events
            self.process_events(events) #Process universally effective events
            for e in events: #Check pygame events
                if e.type==KEYDOWN: #Check for key presses
                    if e.key==MODECHANGE_KEY: #If it is the mode changing key...
                        self.mode+=1 #Increment mode
                        if self.mode>MODES-1: #If (by index) we have exceeded the total number of modes...
                            self.mode=0 #Reset to mode #1 (index 0)
                    elif e.key==START_KEY: #If start key is pressed, end loop
                        waiting=False
            pygame.display.flip() #Update the screen
            fps_clock.tick(FPS)
        if MUSIC_LOADED: #Stop theme music if it loaded properly
            pygame.mixer.music.stop()
            
    def draw_grid(self):
        """Draw the grid"""
        DISPLAY.fill(BACKGROUND_COLOR) #Fill the display, blanking it

        #Draw vertical lines
        for gx in range(GRID_WIDTH):
            pygame.draw.line(DISPLAY, GRID_COLOR, ((gx+1)*GRID_PIX_SIZE, 0), ((gx+1)*GRID_PIX_SIZE, DISP_SIZE[1]))

        #Draw horizontal lines
        for gy in range(GRID_HEIGHT):
            pygame.draw.line(DISPLAY, GRID_COLOR, (0, (gy+1)*GRID_PIX_SIZE), (DISP_SIZE[0], (gy+1)*GRID_PIX_SIZE))
            
    def draw_bikes_at_current(self):
        """Draw bikes at their current actual positions"""
        self.draw_bikes(self.gold_bike.pixpos, self.blue_bike.pixpos)

    def draw_bikes(self, gbp, bbp):
        """Draw the two bikes at the given pixel positions"""
        self.draw_single_bike(gbp[0], gbp[1], GOLD_COLOR)
        self.draw_single_bike(bbp[0], bbp[1], BLUE_COLOR)

    def draw_start_screen(self):
        """Draw the start screen"""
        self.draw_grid() #Draw the game grid
        DISPLAY.blit(TITLE_TEXT, TITLE_TEXT_POS) #Draw title text
        DISPLAY.blit(PRESS_START_TEXT, START_TEXT_POS) #Draw "Press <key> to start" text
        mode_text=MODE_TEXTS[self.mode] #Get appropriate mode text
        DISPLAY.blit(mode_text, MODE_TEXTS_POSS[self.mode]) #Blit mode text
        DISPLAY.blit(MODECHANGE_TEXT, MODECHANGE_TEXT_POS) #Blit modechange text

    def center_text(self, t):
        """Return position to render text so it is centered on the screen"""
        return (int(DISP_SIZE[0]/2-t.get_width()/2+0.5), int(DISP_SIZE[1]/2-t.get_height()/2+0.5))

    def wait_for_key(self, k=None):
        """Wait for a specific or any key to be pressed, updating the display without changes as we do"""
        while True: #Repeat until method returns
            events=pygame.event.get() #Get pygame events
            pygame.display.flip() #Update the display (to prevent freeze-up report, plus I think it's neccesary to get the events)
            self.process_events(events) #Process events for anything applicable to the Game object

            #Go through the events and return if the selected key is pressed. If none was given, return if any key is pressed.
            for e in events:
                if e.type==KEYDOWN and k in (None, e.key):
                    return
                
            fps_clock.tick(FPS) #Tick

    def countdown_to_start(self):
        """Show countdown to game start"""
        for i in range(COUNTDOWN_TIME, 0, -1): #Loop through each second
            #Draw the grid and the bikes. Hmm, using this pair often. Create method?
            self.draw_grid()
            self.draw_bikes_at_current()

            #Create and render time text
            t=LARGE_FONT.render(str(i), False, THECOLORS["white"])
            DISPLAY.blit(t, self.center_text(t))
                
            pygame.display.flip() #Update the display
            time.sleep(1) #Wait one second
            self.process_events(pygame.event.get()) #Process any pygame events

    def process_events(self, events):
        """Process pygame events applicable to the Game object as a whole"""
        for e in events:
            #Check for user quit (the X button or escape key)
            if e.type==QUIT or (e.type==KEYDOWN and e.key==K_ESCAPE):
                pygame.quit()
                quit()

    def draw_out_step(self):
        """Draw out animation of bikes moving from previous position to their current position"""

        #Get bike velocities
        gbv=VELOCITIES[self.gold_bike.facing]
        bbv=VELOCITIES[self.blue_bike.facing]

        #Get old bike pixel positions
        dgbp=self.gold_bike.oldpixpos
        dbbp=self.blue_bike.oldpixpos

        #Step animation anong bikes' trajectories (which will not have changed since the bikes' direction changer is before their moving system in their step method)
        for i in range(0, GRID_PIX_SIZE, BIKE_PIX_SPEED):
            self.draw_grid() #Draw the grid

            #Move each pixel position forward one animation step
            dgbp=(dgbp[0]+BIKE_PIX_SPEED*gbv[0], dgbp[1]+BIKE_PIX_SPEED*gbv[1])
            dbbp=(dbbp[0]+BIKE_PIX_SPEED*bbv[0], dbbp[1]+BIKE_PIX_SPEED*bbv[1])
            
            self.draw_tracks(dgbp, dbbp) #Draw tracks up to current animated position
            self.draw_bikes(dgbp, dbbp) #Draw bikes at current animated position
            pygame.display.flip() #Update the display
            fps_clock.tick(FPS) #Tick

        #Draw all graphic objects using real current bike positions
        self.draw_grid()
        self.draw_tracks()
        self.draw_bikes_at_current()
        
        fps_clock.tick(FPS) #Tick

    def check_winner(self):
        """Check both bikes to see if there is a win or a tie and return None, TIED, or the winning bike's wall string"""
        if self.gold_bike.status==self.blue_bike.status==ALIVE: #Both bikes still alive, so game continues
            return None
        if TIED in self.gold_bike.status+self.blue_bike.status: #Bikes collided, tie
            return TIED
        if self.blue_bike.status==self.gold_bike.status==CRASHED: #Bikes crashed at the same time, tie
            return TIED
        if self.blue_bike.status==CRASHED and self.gold_bike.status==ALIVE: #Gold bike is alive but blue is not, gold wins
            return GOLD_WALL
        if self.gold_bike.status==CRASHED and self.blue_bike.status==ALIVE: #Blue bike is alive but gold is not, blue wins
            return BLUE_WALL

    def draw_tracks(self, gbp=None, bbp=None):
        """Draw the bikes' tracks either out to their current positions or to given pixel positions"""
        #Check if we have been given pixel positions. If not, use the bike's current
        if not gbp:
            gbp=self.gold_bike.pixpos
        if not bbp:
            bbp=self.blue_bike.pixpos

        #Use the bikes' pixel coordinate list of their turns to draw out tracks (Thank You LORD for pygame.draw.lines!)
        pygame.draw.lines(DISPLAY, GOLD_COLOR, False, self.gold_bike.pixturns+[gbp], WALL_WIDTH)
        pygame.draw.lines(DISPLAY, BLUE_COLOR, False, self.blue_bike.pixturns+[bbp], WALL_WIDTH)

        #Draw circles at corners and start to give smooth appearance
        for turn in self.gold_bike.pixturns:
            pygame.draw.circle(DISPLAY, GOLD_COLOR, turn, TURN_RADIUS)
        for turn in self.blue_bike.pixturns:
            pygame.draw.circle(DISPLAY, BLUE_COLOR, turn, TURN_RADIUS)

    def draw_single_bike(self, x, y, color):
        """Draw a single bike graphic at the given position with the given color"""
        pygame.draw.circle(DISPLAY, color, (x, y), BIKE_RADIUS) #Bike's colored center
        pygame.draw.circle(DISPLAY, BIKE_RIM_COLOR,(x, y), BIKE_RADIUS, BIKE_RIM) #Bike's rim

    def declare_winner(self):
        """Declare the game winner, then wait for any key press"""
        #To-Do possibly add markers for each dead bike
        status=self.check_winner() #Check who won
        text=WINNER_TEXTS[status] #Get winner text based on status
        DISPLAY.blit(text, self.center_text(text))
        self.wait_for_key() #Wait for any key press

Game()
#Solo Deo Gloria!
