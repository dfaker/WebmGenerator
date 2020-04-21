# WebmGenerator
UI and Automation to generate high quality VP8 webms in Python3 with ffmpeg and mpv.

*A personal tool, still very sketchy.*

![User Interface](https://raw.githubusercontent.com/dfaker/WebmGenerator/master/ui.png "User Interface")


## External dependencies:
- mpv-1.dll - https://mpv.io/installation/
- ffmpeg - https://www.ffmpeg.org/download.html

Both of these should be placed into the same folder as the script.

## Python dependencies:

numpy==1.18.1

python-mpv==0.3.9

opencv-python==3.4.4.19

tqdm==4.28.1

 `pip3 install -r requirements.txt `

## GUI controls:

On start the program will span a new instance of mpv player and the cool 80s green UI panel.

Clicking and dragging on the black area in the Green UI panel will scrub through the video to select a range.

Scrolling with the mousewheel will increase or decrease the duration of the selected clip.

The player window will loop the currently selected time span.

Pressing **'Q'** or clicking **Queue Current [Q]** will queue the currently selected span to be converted into a webm and restart the current file.

Pressing **'E'** or clicking **Next File [E]** will jump to the next file provided as input if multiple input files are provided.

Pressing **'R'** or clicking **End File Selection [R]** will stop queueing new extracts and close the GUI, the script window will remain open and continue processing until all extracts are converted.

Selecting the player window and pressing **'C'** will activate crop mode, the window will be darkened, click twice to specify the top and bottom corners of your desired cropping rectangle, press **'C'** again to clear the crop.


## Command Examples:

Files or folders may be dragged and dropped directly onto the main.py file or:

`main.py Z:\SomeFolder\TVSeries\`

Scans for all media files in the folder Z:\SomeFolder\TVSeries\ and queues them to be played for clipping into webms

`main.py Z:\SomeFolder\TVSeries\video.mp4`

Queues video.mp4 to be played for clipping into webms

`main.py "EastWorld" Z:\SomeFolder\TVSeries\`

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
