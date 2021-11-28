
local assdraw = require("mp.assdraw")

local dragging = false
local filterIsOn = false
local updateAwaiting = false

local startRecordOnNextLoop = false
local recording = false
local recordingComplete = false

local yaw   = 0.0
local last_yaw = 0.0
local init_yaw = 0.0

local pitch = 0.0
local last_pitch = 0.0
local init_pitch = 0.0

local roll  = 0.0
local last_roll  = 0.0
local init_roll = 0.0

local smoothMouse=true

local inputProjection    = "hequirect"
local outputProjection    = "flat"


local idfov=180.0
local dfov=110.0
local last_dfov  = 110.0
local init_dfov = 0.0

local res  = 5.0

local scaling   = 'linear'

local in_stereo = 'sbs'

local h_flip    = '0'
local in_flip   = ''

local interp    = 'cubic'


local updateComplete = function()
	updateAwaiting = false
end

local writeHeadPositionChange = function()
	
	local newTimePos = mp.get_property("time-pos")

	if pitch ~= last_pitch then
		mp.command(string.format("script-message vrscript setValue pitch %.3f %.3f",newTimePos,pitch))
	end 
	last_pitch=pitch

	if yaw ~= last_yaw then
		mp.command(string.format("script-message vrscript setValue yaw %.3f %.3f",newTimePos,yaw))
	end 
	last_yaw=yaw

	if dfov ~= last_dfov then
		mp.command(string.format("script-message vrscript setValue d_fov %.3f %.3f",newTimePos,dfov))
	end 
	last_dfov=dfov

	if roll ~= last_roll then
		mp.command(string.format("script-message vrscript setValue roll %.3f %.3f",newTimePos,roll))
	end 
	last_roll=roll
end

local updateFilters = function ()
	if not filterIsOn then
		mp.command_native_async({"no-osd", "vf", "add", string.format("@vrrev:%sv360=%s:%s:reset_rot=1:in_stereo=%s:out_stereo=2d:id_fov=%s:d_fov=%.3f:yaw=%.3f:pitch=%s:roll=%.3f:w=%s*192.0:h=%.3f*108.0:h_flip=%s:interp=%s",in_flip,inputProjection,outputProjection,in_stereo,idfov,dfov,yaw,pitch,roll,res,res,h_flip,scaling)}, updateComplete)
		filterIsOn=true
	elseif not updateAwaiting then
		updateAwaiting=true
		mp.command_native_async({"no-osd", "vf", "set", string.format("@vrrev:%sv360=%s:%s:reset_rot=1:in_stereo=%s:out_stereo=2d:id_fov=%s:d_fov=%.3f:yaw=%.3f:pitch=%s:roll=%.3f:w=%s*192.0:h=%.3f*108.0:h_flip=%s:interp=%s",in_flip,inputProjection,outputProjection,in_stereo,idfov,dfov,yaw,pitch,roll,res,res,h_flip,scaling)}, updateComplete)
	end
	if recording then
		writeHeadPositionChange()
	end
end

local mouse_move_cb = function ()
	if dragging then

		local MousePosx, MousePosy = mp.get_mouse_pos()
		local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")


		local yawpc 	= ((MousePosx/osd_w)-0.5)*180
		local pitchpc   = -((MousePosy/osd_h)-0.5)*180

		local updateCrop = false


		if smoothMouse then
			if yaw ~= yawpc and math.abs(yaw-yawpc)<0.1 then
				yaw = yawpc
				updateCrop=true
				yaw = math.max(-180,math.min(180,yaw))
			elseif yaw ~= yawpc then
				yaw   = (yawpc+(yaw*5))/6
				yaw = math.max(-180,math.min(180,yaw))
				updateCrop=true
			end

			if pitch ~= pitchpc and math.abs(pitch-pitchpc)<0.1 then
				pitch = pitchpc
				pitch = math.max(-180,math.min(180,pitch))
				updateCrop=true
			elseif pitch ~= pitchpc then
				pitch = (pitchpc+(pitch*5))/6
				pitch = math.max(-180,math.min(180,pitch))
				updateCrop=true
			end
		else
			if yaw ~= yawpc then 
				yaw  = yawpc
				yaw = math.max(-180,math.min(180,yaw))
				updateCrop=true
			end
			if pitch ~= pitchpc then 
				pitch  = pitchpc
				pitch = math.max(-180,math.min(180,pitch))
				updateCrop=true
			end

		end

		if updateCrop then
			updateFilters()
		end

	end
end

local mouse_btn0_cb = function ()
	dragging = not dragging
	if dragging then
		mp.set_property("cursor-autohide", "always")
	else
		mp.set_property("cursor-autohide", "no")
	end 
end

local reset_and_record = function()
	mp.set_property("time-pos", mp.get_property("ab-loop-a"))
	mp.set_property("pause", "no")
	startRecordOnNextLoop = true
	recording = false
	mp.command(string.format("script-message vrscript resetRecording None None None"))
end



function playback_resetart_cb(event)
    mp.command(string.format("script-message vrscript loopRestart None None None"))
    recordingComplete = false
    if 	startRecordOnNextLoop then
    	recording = true
    	recordingComplete = false
   	else
   		if recording then
   			recordingComplete = true
   		end
   		recording = false
    end
    startRecordOnNextLoop=false

end

function display_status()
	local ass = assdraw.ass_new()
	local la  = mp.get_property("ab-loop-a") 
	local lb  = mp.get_property("ab-loop-b")
	local tp  = mp.get_property("time-pos")

	local playbackpc = 0.0

	if tp ~= nil and tp ~= '' then
		playbackpc = ((tp-la)/(lb-la))*100
	end

	ass:new_event()
	ass:pos(5, 5)
	ass:append("{\\fnUbuntu\\fs4\\b0.3\\bord1}")
	if recording then
		ass:append("{\\c&H00FF00&}- Recording Head Motion -{\\c&HFFFFFF&}\\N")
	else
		ass:append("{\\c&H0000FF&}Not Recording Head Motion{\\c&HFFFFFF&}\\N")
	end

	ass:append(string.format("P=%.3f Y=%.3f Z=%.3f LoopPercent=%.3f%%\\N",pitch,yaw,dfov,playbackpc))
	
	if smoothMouse then
		ass:append("Mouse smoothing on press S toggle.\\N")
	else
		ass:append("Mouse smoothing off press S toggle.\\N")
	end
	ass:append("Press R to restart loop and record motions.\\N")

	if recordingComplete then
		ass:append("{\\c&H00FF00&}Complete motion recording saved.\\N")
	else
		ass:append("{\\c&H0000FF&}Incomplete motion recoding.{\\c&HFFFFFF&}\\N")
	end

	ass:append("Press Q to quit.{\\c&HFFFFFF&}")
	mp.set_osd_ass(0, 0, ass.text)
end

local increment_zoom = function (inc)
	dfov = dfov+inc
	dfov = math.max(math.min(150, dfov), 30)
	updateFilters()
end


local increment_roll = function (inc)
	roll = roll+inc
	roll = math.max(math.min(180, roll), -180)
	updateFilters()
end


local atexit = function()
	mp.command("script-message vrscript exit None None None")
	mp.command("stop")
	mp.command("quit")
end


mp.register_event("playback-restart", playback_resetart_cb)

mp.add_forced_key_binding('space', "toggle_vr360_pause", function() mp.set_property("pause", "no") end )
mp.add_forced_key_binding('q', "toggle_vr360_quit", atexit )
mp.add_forced_key_binding('r', "toggle_vr360_resetandRecord", reset_and_record )
mp.add_forced_key_binding('s', "toggle_vr360_smoothing", function() smoothMouse = not smoothMouse end )
mp.add_forced_key_binding('mouse_btn0', "grab_mouse", mouse_btn0_cb )
mp.add_forced_key_binding('mouse_move', "move_mouse", mouse_move_cb )


mp.add_forced_key_binding('WHEEL_DOWN', "move_mouse_md", function() increment_zoom(1) end )
mp.add_forced_key_binding('WHEEL_UP', "move_mouse_mu", function() increment_zoom(-1) end )

mp.add_forced_key_binding('a', "roll_decrease", function() increment_roll(-1) end )
mp.add_forced_key_binding('d', "roll_increase", function() increment_roll(1) end )

mp.set_property("fullscreen", "yes") 

updateFilters()

mp.add_periodic_timer(0.1, display_status)
