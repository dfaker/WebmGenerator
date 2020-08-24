# WebmGenerator

![Example Output](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/exampleOutput.gif)

## Windows Downloads here https://github.com/dfaker/WebmGenerator/releases

A tool for cutting, filtering and joining video clips, supports webm, mp4 and high quality gif outputs, includes realtime effect filtering and transition effects between scenes.

A large v2 release moving to a more standardized user interface, adds the ability to track the output size of video clip in order to reach some time limit and introduces options to merge clips together into a sequence at the end including cross-filtering transition effects.

## External dependencies:
- mpv-1.dll - https://mpv.io/installation/
- ffmpeg - https://www.ffmpeg.org/download.html

Both of these should be placed into the same folder as the script.

## Python dependencies:

To run with python 3 directly these packages are used:

- python-mpv
- pygubu
- numpy

pip can install them all for you with a single command:

 `pip3 install -r requirements.txt`
 
 For Linux users tkinter may not be installed, to install it in ubuntu for example run: `sudo apt-get install python3-tk`
 
 Alternatively **windows users may use one of the recent bundled releases: https://github.com/dfaker/WebmGenerator/releases.**

## Usage

to start run `webmGenerator.py` or drop video files directly onto `webmGenerator.py`.

### Starting up - Initial Interface

![Initial Interface](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/01%20-%20UI-Initial-Interface.png)

Initially the application opens in the **Cuts** tab, in the left-hand panel you have a Slice settings frame:

- Set `Slice Length` - To set the length of sub clips when they're initially added, you can always resize them later.
- Set the `Target Length` - The final duration you want to hit.
- Set the `Target Trim` - The expected overlap of clips if you use a transition effect to cross-cut between them, if you expect to use hard cuts set this to zero.

Below that are:

- A volume control for playback.
- A status line `00.00s 0.00% (-0.00s)` showing you how many combine seconds you have selected, the percentage to your target duration you're at, and how many seconds are being deducted from the total by the `Target Trim` what we expect adding a 0.25 second cross fade between the clips will deduct.
- A progress indicator to show you how far from hitting target length you are, it turns red when the total of your selected clips exceeds your target length.

Below that is your source videos frame, you can click Load Videos to load one or more source videos for cutting, or quickly clear all of your sub clip selections to start your cut process again.

### Cutting the Clips - Subclip Selection

![Sub clip Selection](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/02%20-%20UI-Clip%20Addition.png)

Once a clip is loaded the bottom dark gray panel changes into a video timeline, you can left click anywhere in it or click and drag to scrub though the video.

Right clicking brings up a context menu that allows you to:

- `Add new subclip` - A new subclip to be cut out will be added to the timeline centered around the point you right clicked, initially it will have the same duration as you set in `Slice Length`
- `Delete subclip` - Removes the subclip under where you right clicked.
- `Add interest mark` - Adds a visual indicator at a time position, no effect on the output but is useful when watching through and decing representative scenes.
- `Nudge to the lowest error +- #s` - Attempts to move the start and end markers (no more than 1 or 2 seconds back and forth) to find a 'perfect loop' for making looping videos, will process in the background and update the subclip under where you right clicked when complete.
- `Run scene change detection` - Starts a background process that searches for any scene transitions in the video and places visual markers on the timeline, this can take quite a while for long clips.

Once a clip has been added you can drag the blue and red start and end markers to change the start and end points of the subclip, the player will seek to whatever position your drag the start or end point to.

The green central bar between the markers may also be dragged to move the whole time window back and forth while keeping the same subclip duration.

Scrolling the mouse wheel on the timeline will zoom in and out, the gray bar at the top of the timeline window may then be used to scrub your zoomed view through the clip to view earlier or later sections.

### Cutting More - Markers and Size Targeting

![Markers and Length Targeting](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/03%20-%20Multiple%20clips%20and%20markers.png)

The above image shows both the presence of the timeline markers added with `Add interest mark` and multiple sub clips that have already been added and resized, Not that with these three sections selected the final output duration is at 74.69 seconds, because this is over the selected `Target Length` the progress bar is red.

### Add Effects - Filtering

![Filtering](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/04%20-%20Filtering.png)

Once all subclips have been defined you may want to use the **Filters** tab to add visual filters, denoising or cropping, but this tab can be skipped if you don't need any filters applied.

The right-hand pane shows you a real-time video preview of what your output will look like with the selected filters applied.

The left-hand pane shows:
- A sub clip navigation block with the current subclip name timespan and where it is in the order of selected clips, the two arrows to the left and right of this block allow you to page through the subclips you've selected.
- Clear, Copy and Paste buttons that will either, remove all filters from the current clip, copy all the filters on the current subclip to a clipboard for later pasting, and paste the currently copied filters onto a new clip.
- A filter selection frame with a drop down of available filters and a button to add the selected filter to the current subclip.

Below that is the stack of filters applied to the current subclip, this clip has had a `hue` adjustment added and a pre-configired `libpostproc` filter for denoising and deblocking poorly encoded video.

Each of the filters may be Removed, Enabled, or moved up and down the filtering order with the buttons that appear below its title, if the filter has any input options they will be displayed as input fields below these buttons, the hue filter in the image for example has been configured to shift the 'h' hue value by 0.42 and increase the 's' saturation value by 3.4.

### Join - Sequencing and Transitions

![Sequencing and Transitions](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/05%20-%20Sequencing%20and%20Transitions.png)

Finally, is the **Merge** tab, If you've not visited it during the current clipping session it'll automatically add all current clips into the sequence on first visit.

The top `Avlaible Cuts` frame shows all of your currently selected sub clips along with a preview of what they'll look like with their applied filters, the button below each is used to add them in to the lower `Sequence` frame.

The `Merge style` drop down allows you to switch between joining all the selected clips together, or outputting them as individual isolated clips.

The `Sequence` panel is the order in which your selected sub clips will appear in the output, the left and right arrow buttons move the sub clips back and forwards in the final video order, the Remove button removes the clip from the planned sequence entirely while keeping it available in the top `Avlaible Cuts` for re-adding later.

The bottom frame the configuration for the output clips:
- `Output filename prefix` - the name that will be added to the start of the final video's filename, this is automatically guessed from the input videos if possible.
- `Output format` - Allows the selection of output format between mpv, webm and gif.
- `Size Match Strategy` - How to handle input videos of difference sizes.
- `Maximum File Size` - The maximum size the output is allowed to be in MB, if the final video is larger than this encoding will be attempted again at a reduced quality (or reduced size for .gifs), if set to zero any output size no matter how large is allowed.
- `Maximum Width` - The maximum output width of the final video, if the output is larger it'll be scaled down, if smaller it'll be left untouched.
- `Transition Duration` - Low long the transition effects between clips will last, if you want hard cuts set this to zero.
- `Transition style` - The look of the transition effects between clips, examples can be seen at https://trac.ffmpeg.org/wiki/Xfade
- `Speed Adjustment` - Will perform a speed-up on the final clip while keeping the sound realistic, a minimum and maximum of 0.5x and 2x are possible but generally becomes distracting over 0.12x

### Make that Video - Encoding

![Encoding](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/06%20-%20Encoding.png)

When you have a sequence you're happy with, you can click 'Encode' to start the encoding process, the progress of the encoding run will be displayed at the bottom as a progress bar, submitted encoding jobs are processed sequentially.

The tool will first make the cuts and apply filters to the subclips and save them in a temporary folder called `tempVideoFiles` this is cleared down after every exit.
After all the clips are cut and filtered they will be joined and if they pass the `Maximum File Size` limit, if any they, will be saved to a folder in the same directory as the script called `finalVideos`, if there is a size limit in place the final encoding step will be repeated using the same `tempVideoFiles` at a lower quality.
