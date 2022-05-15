local msg = require('mp.msg')
local assdraw = require('mp.assdraw')

local script_name = "screenspacetools"
local regmarks = {};

local registrationAss = "";
local mouseAss = "";
local cropAss = "";
local vectorAss = "";


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


function screenspacetools_clear(p1x,p1y,p2x,p2y,fill,border,width,visible)
    cropAss="";
    mouseAss = "";
    draw_merged_ssa()
end

function screenspacetools_drawVector(x1,y1,x2,y2)
    if x1==0 and y1==0 and x2 ==0 and y2 ==0 then
        vectorAss = "";
    else
        local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")

        ass = assdraw.ass_new()
        ass:pos(0,0)
        ass:new_event()
        ass:draw_start()
        ass:pos(0,0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "69dbdbff"))
        ass:append("{\\bord0.5}")

        ass:move_to(tonumber(x1-4), tonumber(y1-4))
        ass:rect_cw(x1-4,y1-4,x1+4,y1+4)

        ass:move_to(tonumber(x1), tonumber(y1))
        ass:line_to(tonumber(x2), tonumber(y2))

        ass:move_to(tonumber(x2-10), tonumber(y2))
        ass:line_to(tonumber(x2+10), tonumber(y2))

        ass:move_to(tonumber(x2), tonumber(y2-10))
        ass:line_to(tonumber(x2), tonumber(y2+10))

        ass:draw_stop()
        ass:pos(0,0)
        vectorAss = ass.text;

    end

    draw_merged_ssa()

end

function screenspacetools_regMark(x,y,type)
    
    if type == "clear" then
        regmarks = {};
    elseif type ~= "" then
        table.insert(regmarks, {px=x,py=y,t=type});
    end


    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")
    
    ass = assdraw.ass_new()




    for k, v in pairs(regmarks) do

        ass:pos(0,0)
        ass:new_event()
        ass:draw_start()
        ass:pos(0,0)

        ass:append(ass_set_color(1, "00000000"))
        if v["t"] == "tvec" then
            ass:append(ass_set_color(3, "ff0000ff"))
            ass:append("{\\bord0.2}")
        else
            ass:append(ass_set_color(3, "69dbdbff"))
            ass:append("{\\bord0.5}")
        end
        
        if v["t"] == "cross" or v["t"] == "tvec" then
            ass:move_to(tonumber(0),     tonumber(v["py"]))
            ass:line_to(tonumber(osd_w), tonumber(v["py"]))
            ass:move_to(tonumber(v["px"]),    tonumber(0))
            ass:line_to(tonumber(v["px"]),    tonumber(osd_h))
        end

        if v["t"] == "cross" or v["t"] == "tvec" then
            ass:move_to(tonumber(v["px"]-15), tonumber(v["py"]))
            ass:line_to(tonumber(v["px"]+15), tonumber(v["py"]))
            ass:move_to(tonumber(v["px"]),    tonumber(v["py"]-15))
            ass:line_to(tonumber(v["px"]),    tonumber(v["py"]+15))
        end


        if v["t"] == "vline" then
            ass:move_to(tonumber(v["px"]), tonumber(0))
            ass:line_to(tonumber(v["px"]), tonumber(osd_h))
        end
        if v["t"] == "hline" then
            ass:move_to(tonumber(0), tonumber(v["py"]))
            ass:line_to(tonumber(osd_w), tonumber(v["py"]))
        end

        ass:draw_stop()
        ass:pos(0,0)

    end


    registrationAss = ass.text;
    draw_merged_ssa()
end

local function ass_escape(str)
    str = str:gsub('\\', '\\\239\187\191')
    str = str:gsub('{', '\\{')
    str = str:gsub('}', '\\}')
    -- Precede newlines with a ZWNBSP to prevent ASS's weird collapsing of
    -- consecutive newlines
    str = str:gsub('\n', '\239\187\191\\N')
    -- Turn leading spaces into hard spaces to prevent ASS from stripping them
    str = str:gsub('\\N ', '\\N\\h')
    str = str:gsub('^ ', '\\h')
    return str
end



function screenspacetools_rect(p1x,p1y,p2x,p2y,dim,fill,border,width,visible)

    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")

    if visible == "outer" then
        ass = assdraw.ass_new()
        ass:new_event()
        ass:pos(0, 0)
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, fill))
        ass:append(ass_set_color(3, border))
        ass:append("{\\bord1}")

        ass:rect_cw(tonumber(p1x), tonumber(p1y), tonumber(p2x), tonumber(p2y))

        ass:pos(0, 0)
        ass:draw_stop()

        mp.set_osd_ass(osd_w, osd_h, ass.text)
    end
    if visible == "inner" then
        ass = assdraw.ass_new()
        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, fill))
        ass:append(ass_set_color(3, "00000000"))

        local l = math.min(tonumber(p1x), tonumber(p2x))
        local r = math.max(tonumber(p1x), tonumber(p2x))
        local u = math.min(tonumber(p1y), tonumber(p2y))
        local d = math.max(tonumber(p1y), tonumber(p2y))

        local midy = tonumber((tonumber(p1x) + tonumber(p2x))/2)
        local midx = tonumber((tonumber(p1y) + tonumber(p2y))/2)

        local thirdx = tonumber(math.abs((tonumber(p1x) - tonumber(p2x)))/3)
        local thirdy = tonumber(math.abs((tonumber(p1y) - tonumber(p2y)))/3)


        ass:rect_cw(0, 0, l, osd_h)
        ass:rect_cw(r, 0, osd_w, osd_h)
        ass:rect_cw(l, 0, r, u)
        ass:rect_cw(l, d, r, osd_h)

        ass:draw_stop()

        -- Draw border around selected region



        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "9F9F9FDD"))
        ass:append("{\\bord1}")

        ass:rect_cw(tonumber(l+thirdx), tonumber(u), tonumber(r-thirdx), tonumber(d))


        ass:draw_stop()


        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "9F9F9FDD"))
        ass:append("{\\bord1}")

        ass:rect_cw(tonumber(l), tonumber(u+thirdy), tonumber(r), tonumber(d-thirdy))


        ass:draw_stop()


        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "9F9F9FAA"))
        ass:append("{\\bord1}")
        ass:rect_cw(tonumber(p1x), tonumber(p1y), tonumber(midy), tonumber(midx))
        ass:draw_stop()


        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "9F9F9FAA"))
        ass:append("{\\bord1}")
        ass:rect_cw(tonumber(midy), tonumber(midx), tonumber(p2x), tonumber(p2y))
        ass:draw_stop()


        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "FF0000FF"))
        ass:append("{\\bord1}")
        ass:rect_cw(tonumber(midy)-15, tonumber(midx)-15, tonumber(midy)+15, tonumber(midx)+15)
        ass:draw_stop()


        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, border))
        ass:append("{\\bord1}")

        ass:rect_cw(tonumber(p1x), tonumber(p1y), tonumber(p2x), tonumber(p2y))
        ass:pos(0, 0)

        ass:draw_stop()

        ass:new_event()


        ass:append(ass_set_color(1, border))
        ass:append(ass_set_color(3, border))

        ass:append("{\\fs18}")
        ass:append("{\\bord0}")
        
        ass:pos(tonumber(p1x), tonumber(p2y))

        ass:append(  ass_escape( dim ))

        ass:pos(0, 0)

        cropAss = ass.text;
        draw_merged_ssa()
    end
end

function draw_merged_ssa()
    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")
    mp.set_osd_ass(osd_w, osd_h, cropAss .. registrationAss .. vectorAss .. mouseAss )
end


function screenspacetools_mouse_cross(x,y)
    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")
    if x==0 and y==0 then
        mouseAss="";
    else
        ass = assdraw.ass_new()

        ass:pos(0,0)
        ass:new_event()
        ass:draw_start()
        ass:pos(0,0)

        ass:append(ass_set_color(1, "00000000"))
        ass:append(ass_set_color(3, "0000ffff"))
        ass:append("{\\bord0.2}")
        
        ass:move_to(tonumber(0),          tonumber(y))
        ass:line_to(tonumber(osd_w),      tonumber(y))
        ass:move_to(tonumber(x),   tonumber(0))
        ass:line_to(tonumber(x),   tonumber(osd_h))

        ass:pos(0,0)
        ass:draw_stop()
        
        mouseAss = ass.text
    end
    draw_merged_ssa()
end

mp.register_script_message("screenspacetools_rect",  screenspacetools_rect)
mp.register_script_message("screenspacetools_clear", screenspacetools_clear)
mp.register_script_message("screenspacetools_regMark", screenspacetools_regMark)
mp.register_script_message("screenspacetools_drawVector", screenspacetools_drawVector)
mp.register_script_message("screenspacetools_mouse_cross", screenspacetools_mouse_cross)
