
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
local smoothFactor = 5

local inputProjection    = "hequirect"
local outputProjection    = "flat"


local idfov=180.0
local dfov=110.0
local last_dfov  = 110.0
local init_dfov = 0.0

local fw=100
local fh=100

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
		mp.command_native_async({"no-osd", "vf", "add", string.format("@vrrev:%sv360=%s:%s:reset_rot=1:in_stereo=%s:out_stereo=2d:id_fov=%s:d_fov=%.3f:yaw=%.3f:pitch=%s:roll=%.3f:w=%.3f:h=%.3f:h_flip=%s:interp=%s",in_flip,inputProjection,outputProjection,in_stereo,idfov,dfov,yaw,pitch,roll,fw,fh,h_flip,scaling)}, updateComplete)
		filterIsOn=true
	elseif not updateAwaiting then
		updateAwaiting=true
		mp.command_native_async({"no-osd", "vf", "set", string.format("@vrrev:%sv360=%s:%s:reset_rot=1:in_stereo=%s:out_stereo=2d:id_fov=%s:d_fov=%.3f:yaw=%.3f:pitch=%s:roll=%.3f:w=%.3f:h=%.3f:h_flip=%s:interp=%s",in_flip,inputProjection,outputProjection,in_stereo,idfov,dfov,yaw,pitch,roll,fw,fh,h_flip,scaling)}, updateComplete)
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
				yaw   = (yawpc+(yaw*smoothFactor))/(smoothFactor+1)
				yaw = math.max(-180,math.min(180,yaw))
				updateCrop=true
			end

			if pitch ~= pitchpc and math.abs(pitch-pitchpc)<0.1 then
				pitch = pitchpc
				pitch = math.max(-180,math.min(180,pitch))
				updateCrop=true
			elseif pitch ~= pitchpc then
				pitch = (pitchpc+(pitch*smoothFactor))/(smoothFactor+1)
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

-- Wrapper that converts RRGGBB / RRGGBBAA to ASS format
local ass_set_color = function (idx, color)
    assert(color:len() == 8 or color:len() == 6)
    local ass = ""

    -- Set alpha value (if present)
    if color:len() == 8 then
        local alpha = 0xff - tonumber(color:sub(7, 8), 16)
        ass = ass .. string.format("\\%da&H%X&", idx, alpha)
    end

    -- Swizzle RGB to BGR and build ASS string
    color = color:sub(5, 6) .. color:sub(3, 4) .. color:sub(1, 2)
    return "{" .. ass .. string.format("\\%dc&H%s&", idx, color) .. "}"
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
	ass:append("{\\fnUbuntu\\fs30\\b1\\bord1}")
	if recording then
		ass:append("{\\c&H00FF00&}- Recording Head Motion -{\\c&HFFFFFF&}\\N")
	else
		ass:append("{\\c&H0000FF&}Not Recording Head Motion{\\c&HFFFFFF&}\\N")
	end

	ass:append(string.format("P=%.3f Y=%.3f Z=%.3f LoopPercent=%.3f%%\\N",pitch,yaw,dfov,playbackpc))
	
	if smoothMouse then
		ass:append(string.format("Mouse smoothing on at factor %.1f press S cycle.\\N",smoothFactor))
	else
		ass:append("Mouse smoothing off press S cycle.\\N")
	end
	ass:append("Press R to restart loop and record motions.\\N")

	if recordingComplete then
		ass:append("{\\c&H00FF00&}Complete motion recording saved.\\N")
	else
		ass:append("{\\c&H0000FF&}Incomplete motion recoding.{\\c&HFFFFFF&}\\N")
	end

	ass:append("Press Q to quit.{\\c&HFFFFFF&}")


    ass:new_event()
    ass:draw_start()
    ass:pos(0, 0)

    ass:append(ass_set_color(1, "000000AA"))
    ass:append(ass_set_color(3, "000000ff"))
    ass:append("{\\bord0}")

    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")

    ass:rect_cw(0, osd_h-10, osd_w, osd_h)


    ass:draw_stop()

    ass:new_event()
    ass:draw_start()
    ass:pos(0, 0)

    ass:append(ass_set_color(1, "0000ffAA"))
    ass:append(ass_set_color(3, "000000ff"))
    ass:append("{\\bord0}")

    ass:rect_cw(0, osd_h-10, osd_w*(playbackpc/100), osd_h)

    ass:draw_stop()
	mp.set_osd_ass(osd_w, osd_h, ass.text)
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

local initialiseValues = function(init_in_proj,init_out_proj,init_in_trans,init_out_trans,init_h_flip,init_ih_flip,init_iv_flip,init_in_stereo,init_out_stereo,init_w,init_h,init_yaw,init_pitch,init_roll,init_d_fov,init_id_fov,init_interp)
	
	inputProjection=init_in_proj
	outputProjection=init_out_proj
	in_stereo=init_in_stereo
	h_flip=init_ih_flip
	fw=init_w
	fh=init_h
	scaling=init_interp
	idfov=init_id_fov
	dfov=init_d_fov

	updateFilters()
end

local incrementSmoothing  = function()

	if smoothFactor == 1 then
		smoothMouse=true
		smoothFactor=5
	elseif smoothFactor < 25 then
		smoothMouse=true
		smoothFactor = smoothFactor+5
	elseif smoothFactor == 25 then
		smoothMouse=false
		smoothFactor=1
	end


end

mp.register_script_message("vrscript_initialiseValues", initialiseValues)

mp.register_event("playback-restart", playback_resetart_cb)

mp.add_forced_key_binding('space', "toggle_vr360_pause", function() mp.set_property("pause", "no") end )
mp.add_forced_key_binding('q', "toggle_vr360_quit", atexit )
mp.add_forced_key_binding('r', "toggle_vr360_resetandRecord", reset_and_record )
mp.add_forced_key_binding('s', "toggle_vr360_smoothing", incrementSmoothing )
mp.add_forced_key_binding('mouse_btn0', "grab_mouse", mouse_btn0_cb )
mp.add_forced_key_binding('mouse_move', "move_mouse", mouse_move_cb )


mp.add_forced_key_binding('WHEEL_DOWN', "move_mouse_md", function() increment_zoom(1) end )
mp.add_forced_key_binding('WHEEL_UP', "move_mouse_mu", function() increment_zoom(-1) end )

mp.add_forced_key_binding('a', "roll_decrease", function() increment_roll(-1) end )
mp.add_forced_key_binding('d', "roll_increase", function() increment_roll(1) end )

mp.set_property("fullscreen", "yes") 

updateFilters()

mp.add_periodic_timer(0.1, display_status)
