# Spotify-Audio-Visualizer
Programming for Digital Arts (Final Project)

# Description
This program will display the current song, artist, timestamp, and album cover of the user's choice of music from their Spotify.
Essentially, this will create a classic audio visualizer with modern elements implemented to give users easy access and customization to their creative desires.

# Features
Ability to change the audio visualizer and background using RGB values 
Ability to change the audio visualizer's shape (blocky, smooth, circles, etc)
Easy linking with the user's Spotify account
UI for changing the colors and a way to exit the program

# Challenges
To link the program with the user's Spotify account, I will study and use the Spotipy library to implement these features. (https://spotipy.readthedocs.io/en/2.25.1/)

The linking process uses the Spotify for Developers portal to create a key that can be pasted into the variables inside the Spotipy library. (https://developer.spotify.com/)

To allow the user to change the colors or exit the program without using specific keybinds, I will also be learning the Pygame GUI library to implement these features so the user can use their mouse inside the program. (https://www.pygame.org/wiki/gui)

(optional) convert the program into an executable that the user can launch without needing to use VSC or other coding software using PyInstaller (https://pyinstaller.org/en/stable/)  

Finally, the audio visualizer. I'll use Pygame, Libriosa, and PyAudio to get the audio information from the user's device.  

# Outcomes

Ideal Outcome:
The outcome I'd like from this project is to create a simple but clean audio visualizer that a user could have running on a separate monitor to provide a more immersive experience to the user whenever they listen to music on their Spotify program.

Minimal Viable Outcome:
If implementing the Spotify features fails, I still want the user to be able to use the audio visualizer for their musical needs. If the audio visualizer fails and the Spotify features get added correctly, the user can still see the song name and time length from the program.

# Milestones
Each week, I'll use the lecture's set date and my current schedule to work on the code for this program.

Here are the steps I will take:
- Create the code for the program to be able to sense different values of frequencies from the device's audio
- Implement specific values on a Band of the audio spectrum that will be implemented
- allow the feature of custom RGB values for the audio spectrum and background
- Implement the Spotipy library to be able to pull data from the user's Spotify account
- put the information onto the surface of the audio spectrum
- (optional) Make the Python program into a runnable exe so the user doesn't need coding software to launch the program.   
  




