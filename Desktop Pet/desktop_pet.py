import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from random import randint, choice
import time

### TO DO ###

# - Add dragging animation
# - fix afterimages (need to ask others for help)
# - add tossing
# - add trampoline

class MainWindow(QMainWindow): #inherit from QMainWindow
    def __init__(self): # dunder init method
        super().__init__() #calling the parent constructor
        self.is_dragging = False  # Track whether the pet is being dragged
        self.fall_speed = 1  # Initialize fall speed
        self.aniamtiontime = 100
        self.height = 0
        self.ground = 620  # y-coordinate of the ground level
        self.horizontal_speed = 5  # pixels per movement step
        self.mouse_start = None
        self.mouse_end = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)#make the window frameless, always on top
        self.setAttribute(Qt.WA_TranslucentBackground, True) #make the window background transparent
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setGeometry(100, self.ground, 200, 200) #x, y, width, height

        # Create label
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 110, 110)
        self.label.setScaledContents(True)

        # Load images in an array of QPixmap objects

        self.frames = []
        
        self.rightframes = [
            QPixmap("rightmove1.png"),
            QPixmap("rightmove2.png"),
            QPixmap("rightmove3.png"),
            QPixmap("rightmove4.png"),
            QPixmap("rightmove5.png"),
            QPixmap("rightmove6.png"),
        ]

        self.leftframes = [
            QPixmap("leftmove1.png"),
            QPixmap("leftmove2.png"),
            QPixmap("leftmove3.png"),
            QPixmap("leftmove4.png"),
            QPixmap("leftmove5.png"),
            QPixmap("leftmove6.png"),]

        self.current_frame = 0
        self.direction = 1  # 1 for right, -1 for left
        self.frames = self.rightframes
        self.test = QPixmap("start.png")
        self.label.setPixmap(self.test)
        self.label.setPixmap(self.frames[self.current_frame])

        # Track mouse position for dragging
        self.drag_position = None

        self.wait_timer = QTimer(self)
        self.wait_timer.timeout.connect(self.move_pet)
        self.wait_timer.start(randint(1000, 7000))  # Start after 1-7 seconds
        # Initialize timers
        self.fall_timer = QTimer(self)
        self.move_timer = QTimer(self)
        self.animation_timer = QTimer(self)


    def move_pet(self):
        self.wait_timer.stop()  # Stop the wait timer

        self.distance_moved = 0
        self.max_distance = randint(50, 150)
        self.direction = choice([-1, 1])

        # Set up a timer for animation
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.movement)
        self.move_timer.start(50)  # switch image every 50ms (0.05s)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.next_frame)
        self.animation_timer.start(self.aniamtiontime)  # switch image every 200ms (0.2s)

        # Stop moving after some time
        def stop_moving():
            self.move_timer.stop()
            self.animation_timer.stop()
            self.wait_timer.start(randint(3000, 7000))  # Restart the wait timer

        def update_distance():
            self.distance_moved += 1 
            if (self.distance_moved >= self.max_distance) and self.current_frame == 1:
                stop_moving()

        self.move_timer.timeout.connect(update_distance)


    def next_frame(self):
        if self.direction == -1:
            self.frames = self.leftframes
        else:
            self.frames = self.rightframes
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.label.setPixmap(self.frames[self.current_frame])
        

    def off_screen_check(self, current_pos):
        new_y = current_pos.y()
        if current_pos.x() > self.screen().geometry().width():  # If it goes off screen, reset to left
            new_x = -20
        elif current_pos.x() < 0:  # If it goes off screen, reset to right
            new_x = self.screen().geometry().width() - 100
        else:
            new_x = current_pos.x() + (1 * self.direction) # Move by 1
        self.move(new_x, new_y)


    def movement(self):
        current_pos = self.pos()
        new_x = current_pos.x() + (1 * self.direction) # Move by 1
        self.off_screen_check(current_pos)

    # Mouse events for dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True  # Set dragging state
            self.stop_all_motion()
            self.press_time = time.time()  # Record the time when mouse is pressed
            self.mouse_start = event.globalPos()
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.last_drag_x = event.globalPos().x()  # Track initial X position
            event.accept()


    def mouseMoveEvent(self, event):
        self.stop_all_motion()

        if event.buttons() & Qt.LeftButton and self.is_dragging and self.drag_position is not None :
            current_x = event.globalPos().x()

            # Check if moving left
            if current_x < self.last_drag_x:
                self.left_drag_animation()

            # Update for next comparison
            self.last_drag_x = current_x

            self.move(event.globalPos() - self.drag_position)
            event.accept()


    def mouseReleaseEvent(self, event):
        # Reset motion state
        self.stop_all_motion()
        self.is_dragging = False  # Reset dragging state
        self.fall_speed = 1
        self.mouse_end = event.globalPos()

        release_time = time.time()
        dt = release_time - self.press_time  # seconds
        dx = self.mouse_end.x() - self.mouse_start.x()

        if dt > 0:
            toss_speed = dx / dt  # pixels per second
        else:
            toss_speed = 0

        self.horizontal_speed = int(toss_speed / 100)  # Scale down for smoother motion

        print(self.horizontal_speed)

        if abs(dx) < 50:
            self.horizontal_speed = 0

        if self.pos().y() < self.ground:
            self.height = self.ground - self.pos().y()
            self.fall_animation()
        else:
            self.move(self.pos().x(), self.ground)
            self.move_timer.start(50)
            self.animation_timer.start(self.aniamtiontime)

        self.drag_position = None
        event.accept()


    def bounce(self):
        # Stop other motion/animation timers 
        self.stop_all_motion()

        # shrink height each bounce
        self.height //= 3
        up_distance = max(2, self.height)

        self.up_start_y = self.pos().y()
        self.up_target_y = max(0, self.up_start_y - up_distance)

        self.up_ticks = max(4, up_distance // 6)
        self.up_tick = 0

        self.up_v0 = (2.0 * (self.up_start_y - self.up_target_y)) / self.up_ticks
        self.up_a = - (self.up_v0) / self.up_ticks

        # Start the bounce timer
        try:
            if self.bounce_timer.isActive():
                self.bounce_timer.stop()
        except AttributeError:
            pass
        self.bounce_timer = QTimer(self)
        self.bounce_timer.timeout.connect(self.up_step)
        self.bounce_timer.start(20)  


    def up_step(self):
        self.up_tick += 1
        n = self.up_tick

        current_pos = self.pos()

        self.off_screen_check(current_pos)

        new_x = current_pos.x() + self.horizontal_speed

        # displacement after n ticks: s = v0*n + 0.5*a*n^2
        disp = (self.up_v0 * n) + (0.5 * self.up_a * (n ** 2))
        new_y = int(self.up_start_y - disp)

        # Clamp/correct and finish when we reached target or exceeded the planned ticks
        if new_y <= self.up_target_y or n >= self.up_ticks:
            self.move(self.pos().x(), self.up_target_y)
            if self.bounce_timer.isActive():
                self.bounce_timer.stop()
            # small delay to avoid timer collision, then start falling
            QTimer.singleShot(30, self.fall_animation)
            return

        self.move(new_x, new_y)


    def fall_animation(self):
        self.fall_timer = QTimer(self)
        self.fall_timer.timeout.connect(self.fall_step)
        self.fall_timer.start(40)  # fall step every 50ms


    def fall_step(self):
        current_pos = self.pos()

        self.off_screen_check(current_pos)

        new_y = current_pos.y() + self.fall_speed
        self.fall_speed += 3  # Increases pixels moved each time function called (simulates acceleration due to gravity)

        new_x = current_pos.x() + self.horizontal_speed

        if new_y >= self.ground:  # Stop falling when it reaches the ground
            new_y = self.ground
            self.fall_timer.stop()
            self.fall_speed = 1  # Reset fall speed
            self.move_timer.start(20)  # Resume moving
            self.animation_timer.start(self.aniamtiontime)  # Resume animation

            # if enough height remains, bounce again
            if self.height > 10:   # stop bouncing once too small
                self.bounce()
            else:
                # resume walking animation
                self.move_timer.start(20)
                self.animation_timer.start(self.aniamtiontime)
            return

        self.move(new_x, new_y)


    def left_drag_animation(self):
        self.animation_timer.start(self.aniamtiontime)


    def stop_all_motion(self):
        if hasattr(self, "move_timer") and self.move_timer.isActive():
            self.move_timer.stop()
        if hasattr(self, "animation_timer") and self.animation_timer.isActive():
            self.animation_timer.stop()
        if hasattr(self, "fall_timer") and self.fall_timer.isActive():
            self.fall_timer.stop()
        if hasattr(self, "bounce_timer") and self.bounce_timer.isActive():
            self.bounce_timer.stop()


    def keyPressEvent(self, event): #overriding keyPressEvent method
        if event.key() == Qt.Key_Q:  # Check if the Q key is pressed
            QApplication.quit()  # Quit the application

def main():
        app = QApplication(sys.argv) #create an instance of QApplication
        # sys.argv allows command line arguments for the application
        window = MainWindow() #create an instance of MainWindow
        window.show() #show the main window
        window.update()
        sys.exit(app.exec_()) #start the application's event loop and keeps the window open


if __name__ == "__main__": #if this file is run directly, call main function to begin!
     main()