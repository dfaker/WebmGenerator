# WebmGenerator


## External dependencies:
- mpv-1.dll - https://mpv.io/installation/
- ffmpeg - https://www.ffmpeg.org/download.html

Both of these should be placed into the same folder as the script.

## Python dependencies:

- python-mpv

 `pip3 install -r requirements.txt`

## Usage

### Initial Interface

![Initial Interface](https://github.com/dfaker/WebmGenerator/blob/version2-tk/DocumentationImages/01%20-%20UI-Initial-Interface.png)

Initially the application appears as above, in the left hand panel you have a Slice settings frame:

- Set `Slcie Length` to control the length of subclips when they're initially added, you can always resize them later.
- Set the `Target Length` - The final duration you want to hit.
- Set the `Target Trim` - The expected overlap of clips if you use a transition effect to cross-cut between them, if you expect to use hard cuts set this to zero.

Below that are:

- A volume control for playback.
- A status line `00.00s 0.00% (-0.00s)` showing you how many combine seconds you have selected, the percentage to your target duration you're at, and how far above or below you are in seconds.
- A progress indicator to show you how far from hitting target length you are, it turns red when the total of your selected clips exceeds your target length.

Below that is your source videos frame, you can click Load Videos to load one or more source videos for cutting, or quickly clear all of your subclip selections to start your cut process again.

### Subclip Selection

![Subclip Selection](https://github.com/dfaker/WebmGenerator/blob/version2-tk/DocumentationImages/02%20-%20UI-Clip%20Addition.png)

### Markers and Size Targeting

![Markers and Length Targeting](https://github.com/dfaker/WebmGenerator/blob/version2-tk/DocumentationImages/03%20-%20Multiple%20clips%20and%20markers.png)

### Filtering

![Filtering](https://github.com/dfaker/WebmGenerator/blob/version2-tk/DocumentationImages/04%20-%20Filtering.png)

### Sequencing and Transitions

![Sequencing and Transitions](https://github.com/dfaker/WebmGenerator/blob/version2-tk/DocumentationImages/05%20-%20Sequencing%20and%20Transitions.png)

### Encoding

![Encoding](https://github.com/dfaker/WebmGenerator/blob/version2-tk/DocumentationImages/06%20-%20Encoding.png)
