# WebmGenerator

![UI Preview](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/UI_preview.gif)

### Windows Downloads here: https://github.com/dfaker/WebmGenerator/releases

A tool for cutting, filtering and joining video clips, supports webm, mp4 and high quality gif outputs, includes realtime effect filtering and transition effects between scenes.

- 🎥 Webm, Mp4 and Gif outputs
- ⏱️ Interactive clip selection powered by mpv
- 📺 Youtube-dl integration to automatically download video from popular sites, incluidng live streams.  
- 🌈 Full suite of filters from cropping to tone mapping and VR to 2D projection.
- 💾 Automatic bitrate adjustment for file size targeting.
- ✂️ Save single extracted clips or join multiple clips into custom edits with transition effects.
- 🍱 Pack multiple videos into dynamically sized grids.

A large v2 release moving to a more standardized user interface, adds the ability to track the output size of video clip in order to reach some time limit and introduces options to merge clips together into a sequence at the end including cross-filtering transition effects.

#### Grid Output
![Grid Example Output](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/GridOutput.gif)

#### Fade Effect Output
![Fade Example Output](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/exampleOutput.gif)

## External dependencies:
- mpv-1.dll - https://mpv.io/installation/
- ffmpeg - https://www.ffmpeg.org/download.html
- youtube-dl - https://ytdl-org.github.io/youtube-dl/ (optional)

All of these should be placed into the same folder as the script or on the PATH.

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
- Set the `Drag offset` - The amount that the current playback location will be shifted back from the end of the subclip (hold ctrl to shift forwards from the start instead) when dragging a preview, large values can be useful in aligning an event between videos.

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
- `Clone subclip` - Duplicates the subclip under where you right clicked.
- `Copy subclip` - Copies the timestamps of the subclip under where you right clicked into an internal clipboard.
- `Paste subclip` - Pastes the timestamps of the subclip under where you right clicked from the internal clipboard, possibly onto a different video.
- `Expand to interest marks` - Extends the the subclip under where you right clicked to that the start and end markers align with the next other interest or scene change markers.
- `Add interest mark` - Adds a visual indicator at a time position, no effect on the output but is useful when watching through and decing representative scenes.
- `Nudge to the lowest error +- #s` - Attempts to move the start and end markers (no more than 1 or 2 seconds back and forth) to find a 'perfect loop' for making looping videos, will process in the background and update the subclip under where you right clicked when complete.
- `Find loop at most #s here` - Scans around where you right clicked on the timeline to find the best 'perfect loop' at most # seconds long.

Once a clip has been added you can drag the blue and red start and end markers to change the start and end points of the subclip, the player will seek to whatever position your drag the start or end point to.

When a start and end marker has been clicked it will remain selected with a white border, the left and right arrow keys can be used to move the selected marker a single frame forwards and backwards for precise start and end point selection.

The green central bar between the markers may also be dragged to move the whole time window back and forth while keeping the same subclip duration.

Scrolling the mouse wheel on the timeline will zoom in and out, the gray bar at the top of the timeline window may then be used to scrub your zoomed view through the clip to view earlier or later sections.

Scrolling the mouse wheel on the green selection bar at the bottom of a subclip will shift that sublcip (both start and end) forwards and backwards while retaining total duration.

### Cutting More - Markers and Size Targeting

![Markers and Length Targeting](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/03%20-%20Multiple%20clips%20and%20markers.png)

The above image shows both the presence of the timeline markers added with `Add interest mark` and multiple sub clips that have already been added and resized, Not that with these three sections selected the final output duration is at 1:56 seconds, because this is over the selected `Target Length` the progress bar is red.

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

As we're in Sequence mode we have two options to control the fade effect between clips, if any:
- `Transition Duration` - Low long the transition effects between clips will last, if you want hard cuts set this to zero.
- `Transition style` - The look of the transition effects between clips, examples can be seen at https://trac.ffmpeg.org/wiki/Xfade

On thw loer frame we have the configuration for the output clips:
- `Output format` - Allows the selection of output format between mpv, webm and gif.
- `Output filename prefix` - the name that will be added to the start of the final video's filename, this is automatically guessed from the input videos if possible.
- `Maximum File Size` - The maximum size the output is allowed to be in MB, if the final video is larger than this encoding will be attempted again at a reduced quality (or reduced size for .gifs), if set to zero any output size no matter how large is allowed.
- `Size Match Strategy` - How to handle input videos of difference sizes.
- `Limit Largest Dimension` - The maximum output width or height of the final video (whichever is greater), if the output is larger it'll be scaled down, if smaller it'll be left untouched.
- `Audio Channels` - Controls the presence or absence of audio in the output, including no sound, and various mono and stereo bitrates.
- `Speed Adjustment` - Will perform a speed-up on the final clip while keeping the sound realistic, a minimum and maximum of 0.5x and 2x are possible but generally becomes distracting over 0.12x

### Make that Video - Encoding

![Encoding](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/06%20-%20Encoding.png)

When you have a sequence you're happy with, you can click 'Encode' to start the encoding process, the progress of the encoding run will be displayed at the bottom as a progress bar, submitted encoding jobs are processed sequentially.

The tool will first make the cuts and apply filters to the subclips and save them in a temporary folder called `tempVideoFiles` this is cleared down after every exit.
After all the clips are cut and filtered they will be joined and if they pass the `Maximum File Size` limit, if any they, will be saved to a folder in the same directory as the script called `finalVideos`, if there is a size limit in place the final encoding step will be repeated using the same `tempVideoFiles` at a lower quality.

### Menu and Options

![Menus](https://github.com/dfaker/WebmGenerator/blob/master/DocumentationImages/07%20-%20Menu%20Options.png)

A number of options and utilities are placed within the three menus at the top of the window:

- `New Project` - Clears all configuration, closes all clips and refreshes for a fresh session.
- `Open Project` - Opens a previously saved project from a *.webmproj file.
- `Save Project` - Saves a previously save project to a *.webmproj file.
- `Run Scene Change Detection` - Scans through the current video looking for scene changes, adds a timeline marker when scene chages are detected.
- `Load Video From Youtube-dl supported URL` - Load a video or stream from any youtube-dl supported site, hudreds of sites supported: https://github.com/ytdl-org/youtube-dl/tree/master/youtube_dl/extractor
- `Load Image as static video` - Load an image as a video clip, will ask that duration the image should be padded out to on load.
- `Watch Clipboard and automatically add urls` - Starts a watcher thread that monitors your clipboard for urls and attempts to download them autoamtically.
- `Cancel Current youtube-dl download` - For live streams in particular the stream may continue for hours after the event you wish to capature, this ends it gracefully and save the file.
- `Update Yuoutube-dl` - As sites change their layouts and apis youtube-dl goes out of date and stops working, this allows you to update with new extractors.
- `Split clip into n equal subclips` - Splits the current video into however many equal subclips you request, good for splitting up long videos where the edit points don't matter.
- `Split clip into sibclips of n seconds` - Similar but cuts the clip into however many sections of n seconds will fit, with the last section being cut shorter if required.
- `Toggle Generation of audio spectra` - Shows the video clips soundwave in the back of the timeline to help with positioning cuts relative to audio events.
- `Clear all clips on current clip` - Clears all of the subclips defined on the current video.
- `Add Subclip by text Range` - Accepts ranges as text for example "1:23 to 1:48.2" or "12s - 13.5s" and adds them as new subclips, a range of formats accepted.


