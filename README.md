# WebmGenerator
UI and Automation to generate high quality VP8 webms

![User Interface](https://raw.githubusercontent.com/dfaker/WebmGenerator/master/ui.png "User Interface")


## External dependencies:
- mpv-1.dll - https://mpv.io/installation/
- ffmpeg - https://www.ffmpeg.org/download.html

Both of these should be placed into the same folder as the script.

## Command Examples:

`main.py Z:\SomeFolder\TVSeries\`

Scans for all media files in the folder Z:\SomeFolder\TVSeries\ and queues them to be played for clipping into webms


`main.py Z:\SomeFolder\TVSeries\video.mp4`

Queues video.mp4 to be played for clipping into webms

`main.py "EastWorld" Z:\SomeFolder\TVSeries\`

Scans for all media files containing the phrase "EastWorld" in the folder Z:\SomeFolder\TVSeries\ and queues them to be played for clipping into webms

## Notes

Processing will run multiple times until it generates a webm between 3.9 and 4.0MB in size, or it tries 10 times and creates a file under 4MB.
Uses multiple pass processing and high quality settings by default so can take quite a while to generate output.
Final files are output into the folder 'out' this will be created if it does not exist.
