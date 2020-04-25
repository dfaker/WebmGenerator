# WebmGenerator
UI and Automation to generate high quality VP8 webms in Python3 with ffmpeg and mpv.

*A personal tool, still very sketchy.*

![User Interface](https://raw.githubusercontent.com/dfaker/WebmGenerator/master/ui.png "User Interface")


## External dependencies:
- mpv-1.dll - https://mpv.io/installation/
- ffmpeg - https://www.ffmpeg.org/download.html

Both of these should be placed into the same folder as the script.

## Python dependencies:

- python-mpv
- opencv-python

 `pip3 install -r requirements.txt`

## Installation Instructions

Get the most recent windows build: https://github.com/dfaker/WebmGenerator/releases or

 - Install Python 3 from https://www.python.org/
 - Download or clone this repository
 - In a command prompt navigate to the folder you cloned this respository into and run the command `pip3 install -r requirements.txt`
 - Download the latest libmpv from https://sourceforge.net/projects/mpv-player-windows/files/libmpv/ extract it and copy the file 'mpv-1.dll' into the same folder you cloned this respository into. 
 - Download the latest ffmpeg build from https://ffmpeg.zeranoe.com/builds/ place ffmpeg.exe into the same folder you cloned this respository into.
 - Drop a file or folder onto webmGenerator.py

## GUI controls:

On start the program will span a new instance of mpv player and the cool 80s green UI panel.

Drag the blue bar to seek in chunks on larger videos, short clips won't need this.

Clicking and dragging on the black area in the Green UI panel will scrub through the video to select a range.

Scrolling with the mousewheel will increase or decrease the duration of the selected clip.

The player window will loop the currently selected time span.

### Upper buttons
Pressing **'Q'** or clicking **Queue Current [Q]** will queue the currently selected span to be converted into a webm and restart the current file.

Pressing **'E'** or clicking **Next File [E]** will jump to the next file provided as input if multiple input files are provided.

Pressing **'R'** or clicking **End File Selection [R]** will stop queueing new extracts and close the GUI, the script window will remain open and continue processing until all extracts are converted.

Pressing **'T'** or clicking **Toggle Logo [T]** to toggle to toggle the top-left corner logo, replace logo.png to set your own.

Pressing **'Y'** or clicking **Toggle Footer [Y]** to toggle to toggle the footer image overlayed at the bottom of the screen, replace footer.png to set your own.



Pressing **'C'** or clicking **Crop [C]** will activate crop mode, the window will be darkened, click twice to specify the top and bottom corners of your desired cropping rectangle, press **'C'** again to clear the crop.

### Lower buttons

Pressing **'1'** or clicking **FPS Limit 30 [1]** will cycle through FPS limits to apply, or turn FPS limiting off.

Pressing **'2'** or clicking **Size Limit 4M [2]** will cycle through maximum file size limits or turn file size limits off.

Pressing **'3'** or clicking **Audio Bitrate 64k [3]** will cycle through options for the audio bitrate to encode at.

Pressing **'4'** or clicking **Max Video Bitrate None [4]** will cycle through the maximum video bitrate to stop at for small files.

Pressing **'5'** or clicking **Max Video Width 1280 [5]** will cycle through the maximum video width to scale output to if larger.

Pressing **'6'** or clicking **Min Video Width 0 [6]** will cycle through the minumum video width to scale output to if smaller.

### Other controls

Playback will start muted to unmute press **'m'** with the player window selected.

Playback will start a 2x normal speed, to reset the speed to 1x press **backpsace** with the player window selected.

All other MPV controls remain as their defaults https://mpv.io/manual/master/.

## Command Examples:

Running webmGenerator.py (Or the webmGenerator.exe id you're using a windows build) will open a file selection prompt, alteratively Files or folders may be dragged and dropped directly onto the webmGenerator.py file or:

`webmGenerator.py Z:\SomeFolder\TVSeries\`

Scans for all media files in the folder Z:\SomeFolder\TVSeries\ and queues them to be played for clipping into webms

`webmGenerator.py Z:\SomeFolder\TVSeries\video.mp4`

Queues video.mp4 to be played for clipping into webms

`webmGenerator.py "EastWorld" Z:\SomeFolder\TVSeries\`

Scans for all media files containing the phrase "EastWorld" in the folder Z:\SomeFolder\TVSeries\ and queues them to be played for clipping into webms

## Notes

Final files are output into the folder 'out' this will be created if it does not exist.

If a filter is provided the output files will be placed into a folder inside 'out' matching the name of the first filter that matched on that file.

The png file 'logo.png' will be placed into the top left corner of the final webm, you can change this to be whatever transparent png you like as long as you keep the filename.

Processing will run multiple times until it generates a webm between 3.9 and 4.0MB in size, or it tries 10 times and creates a file under 4MB.

Uses multiple pass processing and high quality settings by default so can take quite a while to generate output, as a ballpark for a 30 second full resolution clip: 

- 1.5 minutes with two passes for simple source files
- 5 minutes and 4 passes for 4k content.

But these can increase dramatically if seeking deep into high bitrate high resolution streams.
