local msg = require('mp.msg')
local assdraw = require('mp.assdraw')

local script_name = "screenspacetools"

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
    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")
    mp.set_osd_ass(osd_w, osd_h, "")
end

function screenspacetools_rect(p1x,p1y,p2x,p2y,fill,border,width,visible)

    local osd_w, osd_h = mp.get_property("osd-width"), mp.get_property("osd-height")

    if visible == "outer" then
        ass = assdraw.ass_new()
        ass:new_event()
        ass:draw_start()
        ass:pos(0, 0)

        ass:append(ass_set_color(1, fill))
        ass:append(ass_set_color(3, border))
        ass:append("{\\bord1}")

        ass:rect_cw(tonumber(p1x), tonumber(p1y), tonumber(p2x), tonumber(p2y))

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
        ass:append(ass_set_color(3, border))
        ass:append("{\\bord1}")

        ass:rect_cw(tonumber(p1x), tonumber(p1y), tonumber(p2x), tonumber(p2y))

        ass:draw_stop()

        mp.set_osd_ass(osd_w, osd_h, ass.text)
    end
end


mp.register_script_message("screenspacetools_rect",  screenspacetools_rect)
mp.register_script_message("screenspacetools_clear", screenspacetools_clear)
