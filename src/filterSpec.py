
colours = [
  "Black",
  "Gray",
  "White",
  "Black@0.5",
  "White@0.5",  
  "Red",
  "Green",
  "Blue",
  "Pink",
  "Thistle",
  "invert",
  "AliceBlue",
  "AntiqueWhite",
  "Aqua",
  "Aquamarine",
  "Azure",
  "Beige",
  "Bisque",
  "Black",
  "BlanchedAlmond",
  "Blue",
  "BlueViolet",
  "Brown",
  "BurlyWood",
  "CadetBlue",
  "Chartreuse",
  "Chocolate",
  "Coral",
  "CornflowerBlue",
  "Cornsilk",
  "Crimson",
  "Cyan",
  "DarkBlue",
  "DarkCyan",
  "DarkGoldenRod",
  "DarkGray",
  "DarkGreen",
  "DarkKhaki",
  "DarkMagenta",
  "DarkOliveGreen",
  "Darkorange",
  "DarkOrchid",
  "DarkRed",
  "DarkSalmon",
  "DarkSeaGreen",
  "DarkSlateBlue",
  "DarkSlateGray",
  "DarkTurquoise",
  "DarkViolet",
  "DeepPink",
  "DeepSkyBlue",
  "DimGray",
  "DodgerBlue",
  "FireBrick",
  "FloralWhite",
  "ForestGreen",
  "Fuchsia",
  "Gainsboro",
  "GhostWhite",
  "Gold",
  "GoldenRod",
  "Gray",
  "Green",
  "GreenYellow",
  "HoneyDew",
  "HotPink",
  "IndianRed",
  "Indigo",
  "Ivory",
  "Khaki",
  "Lavender",
  "LavenderBlush",
  "LawnGreen",
  "LemonChiffon",
  "LightBlue",
  "LightCoral",
  "LightCyan",
  "LightGoldenRodYellow",
  "LightGreen",
  "LightGrey",
  "LightPink",
  "LightSalmon",
  "LightSeaGreen",
  "LightSkyBlue",
  "LightSlateGray",
  "LightSteelBlue",
  "LightYellow",
  "Lime",
  "LimeGreen",
  "Linen",
  "Magenta",
  "Maroon",
  "MediumAquaMarine",
  "MediumBlue",
  "MediumOrchid",
  "MediumPurple",
  "MediumSeaGreen",
  "MediumSlateBlue",
  "MediumSpringGreen",
  "MediumTurquoise",
  "MediumVioletRed",
  "MidnightBlue",
  "MintCream",
  "MistyRose",
  "Moccasin",
  "NavajoWhite",
  "Navy",
  "OldLace",
  "Olive",
  "OliveDrab",
  "Orange",
  "OrangeRed",
  "Orchid",
  "PaleGoldenRod",
  "PaleGreen",
  "PaleTurquoise",
  "PaleVioletRed",
  "PapayaWhip",
  "PeachPuff",
  "Peru",
  "Pink",
  "Plum",
  "PowderBlue",
  "Purple",
  "Red",
  "RosyBrown",
  "RoyalBlue",
  "SaddleBrown",
  "Salmon",
  "SandyBrown",
  "SeaGreen",
  "SeaShell",
  "Sienna",
  "Silver",
  "SkyBlue",
  "SlateBlue",
  "SlateGray",
  "Snow",
  "SpringGreen",
  "SteelBlue",
  "Tan",
  "Teal",
  "Thistle",
  "Tomato",
  "Turquoise",
  "Violet",
  "Wheat",
  "White",
  "WhiteSmoke",
  "Yellow",
  "YellowGreen",
]


fonts = [
  'System', 
  'Terminal', 
  'Fixedsys', 
  'Modern', 
  'Roman', 
  'Script', 
  'Courier', 
  'Arial',
  'Consolas',
  'Courier New',
  'Lucida Console',
  'Symbol', 
  'Tahoma',
  'Trebuchet MS',
  'Droid Serif', 
  'Droid Sans', 
  'Droid Sans Mono', 
  'DejaVu Sans Condensed', 
  'DejaVu Sans', 
  'DejaVu Sans Mono'
]

selectableFilters = [


    {
        "name": "drawbox",
        "filter": "drawbox@{fn}",
        "category":'Overlays, text and masks',
        "timelineSupport":True,
        "params": [
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "videoSpaceAxis":"x",
                "videoSpaceSign":1,
                "inc": 1,
                "commandVar":['Box-X',[['drawbox@{fn}','x']]]
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "videoSpaceAxis":"y",
                "videoSpaceSign":1,
                "inc": 1,
                "commandVar":['Box-Y',[['drawbox@{fn}','y']]]
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
                "commandVar":['Box-Width',[['drawbox@{fn}','w']]]
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
                "commandVar":['Box-Height',[['drawbox@{fn}','h']]]
            },
            {
                "n": "t",
                "d": "fill",
                "type": "cycle",
                "cycle": ["fill", "1", "2", "5", "w/3" "w/5" "w/10"],
            },
            {
                "n": "color",
                "d": "Black",
                "type": "cycle",
                "cycle": colours,
            },
        ],
    },

  {
        "name": "crop",
        "category":'Resizing and Cropping',
        "desc":"Crops the video frame in a from point x,y out to a width and height w and h",
        "filter": "crop@{fn}",
        "params": [
            {
                "n": "x",
                "d": 0,
                "type": "int",
                "range": None,
                "rectProp": "x",
                "videoSpaceAxis":"x",
                "videoSpaceSign":1,
                "inc": 1,
                "commandVar":['Crop-X',[['crop@{fn}','x']]]
            },
            {
                "n": "y",
                "d": 0,
                "type": "int",
                "range": None,
                "rectProp": "y",
                "videoSpaceAxis":"y",
                "videoSpaceSign":1,
                "inc": 1,
                "commandVar":['Crop-Y',[['crop@{fn}','y']]]
            },
            {
                "n": "w",
                "d": 100,
                "type": "int",
                "range": None,
                "rectProp": "w",
                "inc": 10,
                "commandVar":['Crop-W',[['crop@{fn}','w']]]
            },
            {
                "n": "h",
                "d": 100,
                "type": "int",
                "range": None,
                "rectProp": "h",
                "inc": 10,
                "commandVar":['Crop-H',[['crop@{fn}','h']]]
            }
        ],
    },
{
  
        "name": "vhsconv",
        "category":'Filter Effects',
        "filter": "convolution='-2 -1 0 -1 1 1 0 1 2:-2 -1 0 -1 1 1 0 1 2:-2 -1 0 -1 1 1 0 1 2:-2 -1 0 -1 1 1 0 1 2'",

},

    {
        "name": "scaleDown",
        "category":'Resizing and Cropping',
        "filter": "scale=w=iw*{factor}:h=ih*{factor}:sws_flags=area",
        "params": [
            {"n": "factor","desc":"Reduction factor", "d": 1.0, "type": "float", "range": [0, 1], "inc": 0.005}
            ]
    },


 {
        "name": "mpdecimate",
        "category":'Frame Rate and Decimation',
        "filter":"mpdecimate",
        "params": [
            {
                "n": "max",
                "d": 1,
                "type": "int",
                "range": [None,None],
                "inc": 1,
            },
            {
                "n": "hi",
                "d": 768,
                "type": "int",
                "range": [None,None],
                "inc": 1,
            },
            {
                "n": "lo",
                "d": 320,
                "type": "int",
                "range": [None,None],
                "inc": 1,
            },
            {
                "n": "frac",
                "d": 0.33,
                "type": "int",
                "range": [None,None],
                "inc": 0.1,
            }
        ]
 },


 {
        "name": "decimate",
        "category":'Frame Rate and Decimation',
        "filter":"decimate",
        "params": [
            {
                "n": "cycle",
                "d": 5,
                "type": "int",
                "range": [1,None],
                "inc": 1,
            },
            {
                "n": "dupthresh",
                "d": 1.1,
                "type": "float",
                "range": [0,None],
                "inc": 0.1,
            },
            {
                "n": "scthresh",
                "d": 15,
                "type": "int",
                "range": [0,None],
                "inc": 1,
            }
        ]
 },


{
        "name": "fillborders",
        "category":'Resizing and Cropping',
        "params": [
            {
                "n": "left",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "right",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "top",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "bottom",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "mode",
                "d": "smear",
                "type": "cycle",
                "cycle": ["smear","mirror","fixed","reflect","wrap","fade","margins"],
            }
        ],
    },

 {
        "name": "Pad - Pad Borders",
        "category":'Resizing and Cropping',
        "filter": "pad=x={left}:y={top}:w=iw+{left}+{right}:h=ih+{top}+{bottom}:color={color}",
        "params": [
            {
                "n": "top",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "right",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "bottom",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "left",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "inc": 1,
            },
            {
                "n": "color",
                "d": "Black",
                "type": "cycle",
                "cycle": colours,
            }
        ],
    },

 {
        "name": "Pad - Place Frame in Padding",
        "category":'Resizing and Cropping',
        "filter": "pad@{fn}",
        "params": [
            {
                "n": "x",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "rectProp": "x",
                "inc": 1,
                "commandVar":['Origin-X',[['pad@{fn}','x']]]
            },
            {
                "n": "y",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "rectProp": "y",
                "inc": 1,
                "commandVar":['Origin-Y',[['pad@{fn}','y']]]
            },
            {
                "n": "w",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": 10,
                "type": "float",
                "range": [0,None],
                "rectProp": "h",
                "inc": 1,
            },
            {
                "n": "color",
                "d": "Black",
                "type": "cycle",
                "cycle": colours,
            }
        ],
    },

 {
        "name": "lagfun",
        "filter": "lagfun",
        "params": [
            {
                "n": "decay",
                "d": 0.95,
                "type": "float",
                "range": [0, 1],
                "inc": 0.1,
            },
            {
                "n": "planes",
                "d": 15,
                "type": "int",
                "range": [0,15],
                "inc": 1,
            }
        ],
    },

    {
      "name":"perspective",
      "category":'Resizing and Cropping',
      "filter":"pad=iw+4:ih+4:2:2:{bgColor},perspective=x0={x0}:y0={y0}:x1={x1}:y1={y1}:x2={x2}:y2={y2}:x3={x3}:y3={y3}:interpolation={interpolation}:sense={sense}",
      "params": [
            {"n": "x0","d": 0,"type": "float","range": None,"inc": 1,  "rectProp": "px0"},
            {"n": "y0","d": 0,"type": "float","range": None,"inc": 1,  "rectProp": "py0"},
            {"n": "x1","d": 100,"type": "float","range": None,"inc": 1,"rectProp": "px1"},
            {"n": "y1","d": 0,"type": "float","range": None,"inc": 1,  "rectProp": "py1"},
            {"n": "x2","d": 0,"type": "float","range": None,"inc": 1,  "rectProp": "px2"},
            {"n": "y2","d": 100,"type": "float","range": None,"inc": 1,"rectProp": "py2"},
            {"n": "x3","d": 100,"type": "float","range": None,"inc": 1,"rectProp": "px3"},
            {"n": "y3","d": 100,"type": "float","range": None,"inc": 1,"rectProp": "py3"},
            {
                "n": "sense",
                "d": "destination",
                "type": "cycle",
                "cycle": [
                    "destination",
                    "source"
                ],
            },
            {
                "n": "interpolation",
                "d": "linear",
                "type": "cycle",
                "cycle": ["linear","cubic"],
            },
            {
                "n": "bgColor",
                "d": "DarkGray",
                "type": "cycle",
                "cycle": colours,
            }

      ]
    },


    {
        "name": "zoomPiP",
        
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vinb{fn}]null[bg{fn}],[vina{fn}]crop@{fn}=w={w}:h={h}:x={x}:y={y},scale@{fn}=iw*{zoom}:ih*{zoom}[fg{fn}],[bg{fn}][fg{fn}]overlay@{fn}=x={outX}:y={outY}",
        "params": [ 
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
                "commandVar":['Crop-X',[['crop@{fn}','x']]]
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
                "commandVar":['Crop-Y',[['crop@{fn}','y']]]
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
                "commandVar":['Crop-W',[['crop@{fn}','w']]]
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
                "commandVar":['Crop-h',[['crop@{fn}','h']]]
            },
            {
                "n": "zoom",
                "d": 1,
                "type": "float",
                "range": [0, None],
                "inc": 0.1,
            },
            {
                "n": "outX",
                "d": 1,
                "type": "int",
                "range": None,
                "inc": 1,
                "commandVar":['Overlay-x',[['overlay@{fn}','x']]]
            },
            {
                "n": "outY",
                "d": 1,
                "type": "int",
                "range": None,
                "inc": 1,
                "commandVar":['Overlay-Y',[['overlay@{fn}','y']]]
            }
        ],
    },

    {
        "name": "hueOutsideArea",
        "timelineSupport":True,
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vinb{fn}]hue=h={h}:s={s}:b={b}[bg{fn}],[vina{fn}]crop={w}:{ch}:{x}:{y}[fg{fn}],[bg{fn}][fg{fn}]overlay={x}:{y}",
        "params": [
            {"n": "h", "d": 0, "type": "float", "range": [0, 360], "inc": 0.0174533},
            {"n": "s", "d": 2, "type": "float", "range": [-10, 10], "inc": 0.2},
            {"n": "b", "d": 0, "type": "float", "range": [-10, 10], "inc": 0.2},     
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "ch",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            }
        ],
    },


{'desc': 'Scale the input using EPX algorithm.',
 "category":'Resizing and Cropping',
 'filter': 'epx',
 'kind': 'V->V',
 'name': 'epx',
 'params': [{'d': 3.0, 'inc': 1, 'n': 'n', 'range': [2.0, 3.0], 'type': 'int'}],
 'support': '.S.'}
,

    {
        "name": "transText",
        "filter": "null[vin{fn}],color=s={w}x{h}:c=black[cbg],color=c=white:s={w}x{h}[abg],[abg]drawtext=text={text}:fontsize={fontsize}:x={x}:y={y}:fontfile='{fontfile}':fontcolor=black[cbox],[cbg][cbox]alphamerge[c],[vin{fn}][c]overlay=eval=init",
        
        "filterPreview": "drawbox=c=black:x=0:y=0:w={w}:h={h},drawtext=text={text}:fontsize={fontsize}:x={x}:y={y}:fontfile='{fontfile}':fontcolor=red",


        "params": [ 

            {"n": "text", "d": "Text", "type": "string"},
            {"n": "fontfile", "d": "resources/quicksand.otf", "type": "file", "fileCategory":"font"},

            {"n": "w", "d": 1, "type": "int", "range": None, "rectProp": "w", "inc": 1},
            {"n": "h", "d": 1, "type": "int", "range": None, "rectProp": "h", "inc": 1},

            {"n": "x", "d": 1, "type": "int", "range": None, "rectProp": "x", "inc": 1},
            {"n": "y", "d": 1, "type": "int", "range": None, "rectProp": "y", "inc": 1},
            {"n": "fontsize", "d": 1, "type": "int", "range": None, "inc": 1},



        ],
    },

    {
        "name": "negate",        
        "filter": "negate",
    },


    {
        "name": "colortemperature",
        "filter": "colortemperature",
        "params": [
            {"n": "temperature", "d": 6500 , "type": "int", "range": [1000, 40000], "inc": 100}, 
            {"n": "mix", "d": 1, "type": "float", "range": [0, 1], "inc": 0.01}, 
            {"n": "pl", "d": 0, "type": "float", "range": [0, 1], "inc": 0.01}, 

        ],
    },

    {
        "name": "colorcontrast",
        "filter": "colorcontrast",
        "params": [
            {"n": "rc", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01}, 
            {"n": "gm", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01},
            {"n": "by", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01},
            {"n": "rcw", "d": 0.0 , "type": "float", "range": [0, 1], "inc": 0.01}, 
            {"n": "rcw", "d": 0.0 , "type": "float", "range": [0, 1], "inc": 0.01},
            {"n": "rcw", "d": 0.0 , "type": "float", "range": [0, 1], "inc": 0.01},
            {"n": "pl", "d": 0, "type": "float", "range": [0, 1], "inc": 0.01},
        ],
    },

    {
        "name": "colorcorrect",
        "filter": "colorcorrect",
        "params": [
            {"n": "rl", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01}, 
            {"n": "bl", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01},
            {"n": "rh", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01},
            {"n": "bh", "d": 0.0 , "type": "float", "range": [-1, 1], "inc": 0.01}, 

            {"n": "saturation", "d": 1.0 , "type": "float", "range": [-3, 3], "inc": 0.01},
            {
                "n": "analyze",
                "d": "manual",
                "type": "cycle",
                "cycle": ["manual","average","minmax","median"],
            },

        ],
    },








    {
        "name": "reverse",
        "desc":"Warning! This filter will not show in preview, but ffmpeg will need to buffer the entire original clip, easily using all system memory, consider pre-cutting before applying this.",
        "filter": "reverse",
        "filterPreview":"null"
    },


    {
        "name": "amplify",
        "filter": "amplify",
        "params": [
            {"n": "radius", "d": 2, "type": "int", "range": [1, 63], "inc": 1}, 
            {"n": "factor", "d": 2, "type": "int", "range": [0, 65535], "inc": 1}, 

        ],
    },


    {
        "name": "vibrance",
        "filter": "vibrance",
        "params": [
            {"n": "intensity", "d": 0.5, "type": "float", "range": [-2, 2], "inc": 0.05}, 
            {"n": "rbal", "d": 1, "type": "float", "range": [-2, 2], "inc": 0.05}, 
            {"n": "gbal", "d": 1, "type": "float", "range": [-2, 2], "inc": 0.05}, 
            {"n": "bbal", "d": 1, "type": "float", "range": [-2, 2], "inc": 0.05}, 

            {"n": "rlum", "d": 0, "type": "float", "range": [-2, 2], "inc": 0.05}, 
            {"n": "glum", "d": 0, "type": "float", "range": [-2, 2], "inc": 0.05}, 
            {"n": "blum", "d": 0, "type": "float", "range": [-2, 2], "inc": 0.05}, 

        ],
    },

    {
        "name": "hueInsideArea",
        "timelineSupport":True,
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vina{fn}]crop={w}:{h}:{x}:{y},hue=h={ch}:s={cs}:b={cb}[fg{fn}],[vinb{fn}][fg{fn}]overlay={x}:{y}",
        "params": [
            {"n": "ch", "d": 0, "type": "float", "range": [0, 360], "inc": 0.0174533},
            {"n": "cs", "d": 2, "type": "float", "range": [-10, 10], "inc": 0.2},
            {"n": "cb", "d": 0, "type": "float", "range": [-10, 10], "inc": 0.2},     
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            }
        ],
    },


    {
        "name": "posterizeArea",
        "timelineSupport":True,
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vina{fn}]crop={w}:{h}:{x}:{y},elbg=codebook_length={strength}:nb_steps={nb_steps}[fg{fn}],[vinb{fn}][fg{fn}]overlay={x}:{y}",
        "params": [
            {
                "n": "strength",
                "d": 10,
                "type": "int",
                "range": None,
                "inc": 1,
            },         
            {
                "n": "nb_steps",
                "d": 1,
                "type": "int",
                "range": None,
                "inc": 1,
            },       
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            }
        ],
    },


  {
        "name": "gaussianBlur",
        "timelineSupport":True,
        "filter": "gblur@{fn}",
        "params": [
            {
                "n": "sigma",
                "d": 20,
                "type": "int",
                "range": None,
                "inc": 1,
                "commandVar":['GBlur-Sigma',[['gblur@{fn}','sigma']]]
            },
            {
                "n": "steps",
                "d": 1,
                "type": "int",
                "range": None,
                "inc": 1,
                "commandVar":['GBlur-Steps',[['gblur@{fn}','steps']]]
            },
        ]
  },


  {
        "name": "gaussianBlurArea",
        "timelineSupport":True,
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vina{fn}]crop@{fn}=w={w}:h={h}:x={x}:y={y},gblur={strength}:steps={steps}[fg{fn}],[vinb{fn}][fg{fn}]overlay@{fn}={x}:{y}",
        "params": [
            {
                "n": "strength",
                "d": 20,
                "type": "int",
                "range": None,
                "inc": 1,
            },
            {
                "n": "steps",
                "d": 1,
                "type": "int",
                "range": None,
                "inc": 1,
            },             
            {

                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
                "commandVar":['Box-X',[['crop@{fn}','x'],['overlay@{fn}','x']]]
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
                "commandVar":['Box-Y',[['crop@{fn}','y'],['overlay@{fn}','y']]]
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
                "commandVar":['Box-Width',[['crop@{fn}','w']]]
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
                "commandVar":['Box-Height',[['crop@{fn}','h']]]
            }
        ],
    },


    {
        "name": "vflipArea",
        "timelineSupport":True,
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vina{fn}]crop={w}:{h}:{x}:{y},vflip[fg{fn}],[vinb{fn}][fg{fn}]overlay={x}:{y}",
        "params": [          
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            }
        ],
    },


    {
        "name": "boxBlurArea",
        "timelineSupport":True,
        "filter": "null[vin{fn}],[vin{fn}]split=2[vina{fn}][vinb{fn}],[vina{fn}]crop={w}:{h}:{x}:{y},boxblur={strength}[fg{fn}],[vinb{fn}][fg{fn}]overlay={x}:{y}",
        "params": [
            {
                "n": "strength",
                "d": 20,
                "type": "float",
                "range": None,
                "inc": 1,
            },            
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            }
        ],
    },

    {
        "name": "subtitles",
        "filter": "subtitles=filename='{filename}':force_style='Fontname={fontname},Fontsize={fontsize},PrimaryColour={primaryColour},OutlineColour={outlineColour},Outline={outlineWidth},BackColour={shadowColour},Shadow={outlineShadowWidth}'",
        "params": [
            {"n": "filename", "d": "subtitles.srt", "type": "file", "fileCategory":"subtitle"},
            {"n": "fontname", "d": "", "type": "cycle",
                "cycle": [""]+fonts,
            },

            {"n": "fontsize", "d": 12, "type": "float", "range": [0, None], "inc": 0.1},
            {"n": "primaryColour", "d": "&H0000CCFF", "type": "bareString"},
            {"n": "outlineColour", "d": "&H00000000", "type": "bareString"},
            {"n": "shadowColour", "d": "&H00000000", "type": "bareString"},
            {"n": "outlineWidth", "d": 1, "type": "float", "range": [0, None], "inc": 0.1},
            {"n": "outlineShadowWidth", "d": 0, "type": "float", "range": [0, None], "inc": 0.1}

        ],
    },

    {"name": "normalize", "filter": "normalize"},
    


    {
        "name": "fade",
        "filter": "fade",
        "params": [
            {
                "n": "type",
                "d": "in",
                "type": "cycle",
                "cycle": ["in", "out"],
            },

            {"n": "duration", "d": 1, "type": "float", "range": [0, None], "inc": 0.1},
            {"n": "start_time", "d": 1, "type": "float", "range": [0, None], "inc": 0.1},


            {
                "n": "color",
                "d": "Black",
                "type": "cycle",
                "cycle": colours,
            }

        ],
    },





    {
        "name": "minterpolate",
        "filter": "minterpolate",
        "params": [
            {"n": "fps", "d": 60, "type": "float", "range": [1, None], "inc": 1},
            {
                "n": "mi_mode",
                "d": "mci",
                "type": "cycle",
                "cycle": ["mci", "dup", "blend"],
            },
            {
                "n": "me_mode",
                "d": "bidir",
                "type": "cycle",
                "cycle": ["bidir", "bilat"],
            },
            {
                "n": "me",
                "d": "esa",
                "type": "cycle",
                "cycle": ["esa", "bilat", "tss", "tdls", "ntss", "fss", "ds", ""],
            },
            {"n": "mb_size", "d": 16, "type": "float", "range": [1, None], "inc": 1},
        ],
    },
    
    {"name": "libpostproc+temportaldenoiser", "filter": "pp=default/tmpnoise|1|2|3"},
    
    {"name": "libpostproc-deblock+dering+contrast", "filter": "pp=hb/vb/dr/al"},
    
    {
        "name": "v360 - VR Correction",
        "timelineSupport":True,
        "filter": "v360@{fn}={in_proj}:{out_proj}:in_stereo={in_stereo}:out_stereo={out_stereo}:id_fov={id_fov}:yaw={yaw}:pitch={pitch}:roll={roll}:d_fov={d_fov}:w={w}:h={h}:interp={interp}:in_trans={in_trans}:out_trans={out_trans}:h_flip={h_flip}:ih_flip={ih_flip}:iv_flip={iv_flip}:alpha_mask=1",
        "params": [
            {
                "n": "in_proj",
                "d": "hequirect",
                "type": "cycle",
                "cycle": [
                    "sg",
                    "fisheye",
                    "ball",
                    "equirect",
                    "hequirect",
                    "rectilinear",
                    "pannini",
                    "cylindrical",
                ],
            },
            {
                "n": "out_proj",
                "d": "flat",
                "type": "cycle",
                "cycle": [
                    "sg",
                    "fisheye",
                    "ball",
                    "flat",
                    "rectilinear",
                    "pannini",
                    "cylindrical",
                ],
            },
            {"n": "in_trans", "d": "0", "type": "cycle", "cycle": ["1", "0",]},
            {"n": "out_trans", "d": "0", "type": "cycle", "cycle": ["1", "0",]},
            {"n": "h_flip", "d": "0", "type": "cycle", "cycle": ["1", "0",]},
            {"n": "ih_flip", "d": "0", "type": "cycle", "cycle": ["1", "0",]},
            {"n": "iv_flip", "d": "0", "type": "cycle", "cycle": ["1", "0",]},
            {
                "n": "in_stereo",
                "d": "sbs",
                "type": "cycle",
                "cycle": ["sbs", "2d", "tb"],
            },
            {
                "n": "out_stereo",
                "d": "2d",
                "type": "cycle",
                "cycle": ["sbs", "2d", "tb"],
            },
            {"n": "w", "d": 100, "type": "float", "range": None, "inc": 10},
            {"n": "h", "d": 100, "type": "float", "range": None, "inc": 10},


            {"n": "yaw", "d": 0.0, "type": "float", "range": [-90, 90],     "inc": 1,
             "videoSpaceAxis":"yaw",
             "videoSpaceSign":1,
             "interpMode":"neighbour-relative",
             "restrictedInterpModes":["neighbour-relative"],
             "commandVar":['VR-Yaw',[['v360@{fn}','yaw']]]},
            
            {"n": "pitch", "d": 0.0, "type": "float", "range": [-90, 90],   "inc": 1,
             "videoSpaceAxis":"pitch",
             "videoSpaceSign":-0.5,
            "interpMode":"neighbour-relative",
            "restrictedInterpModes":["neighbour-relative"],
            "commandVar":['VR-Pitch',[['v360@{fn}','pitch']]]},
            
            {"n": "roll", "d": 0.0, "type": "float", "range": [-180, 180],  "inc": 1,
            "interpMode":"neighbour-relative",
            "restrictedInterpModes":["neighbour-relative"],
            "commandVar":['VR-Roll',[['v360@{fn}','roll']]]},
            


            {"n": "d_fov", "d": 90.0, "type": "float", "range": [0, 180],   "inc": 1   ,"commandVar":['VR-OutFOV',[['v360@{fn}','d_fov']]]},
            {"n": "id_fov", "d": 180.0, "type": "float", "range": [0, 180], "inc": 1 ,"commandVar":['VR-InFOV',[['v360@{fn}','id_fov']]]},
            {
                "n": "interp",
                "d": "nearest",
                "type": "cycle",
                "cycle": ["nearest","linear", "lagrange9", "cubic", "spline16", "gaussian","mitchell"],
            },
        ],
    },


    {
        "name": "Overlay",
        "timelineSupport":True,
        "filter": "null[vin{fn}],movie='{source}':loop=1,scale=w={w}:h={h},format=argb,colorchannelmixer@{fn}=aa={alpha},rotate@{fn}=a={angle}:out_w=rotw({angle}):out_h=roth({angle}):fillcolor=none[pwm{fn}],[vin{fn}][pwm{fn}]overlay@{fn}=x={x}:y={y}",
        "filterPreview": "null[vin{fn}],movie='{source}',scale=w={w}:h={h},format=argb,colorchannelmixer@{fn}=aa={alpha},rotate@{fn}=a={angle}:out_w=rotw({angle}):out_h=roth({angle}):fillcolor=none[pwm{fn}],[vin{fn}][pwm{fn}]overlay@{fn}=x={x}:y={y}",
        "params": [
            {"n": "source", "d": "resources/logo.png", "type": "file", "fileCategory":"image"},
            {
                "n": "x",
                "d": 5,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
                "commandVar":['Overlay-X',[['overlay@{fn}','x']]]
            },
            {
                "n": "y",
                "d": 5,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
                "commandVar":['Overlay-Y',[['overlay@{fn}','y']]]
            },
            {
                "n": "w",
                "d": -1,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,

            },
            {
                "n": "h",
                "d": -1,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            },
            {
                "n": "angle",
                "d": 0.0,
                "type": "float",
                "range": [-6.28319, 6.28319],
                "inc": 0.0174533,
                "commandVar":['Overlay-Rotation',[['rotate@{fn}','a']]]
            },
            {
                "n": "alpha",
                "d": 1.0,
                "type": "float",
                "range": [0.0, 1.0],
                "inc": 0.01,
                "commandVar":['Overlay-Transparency',[['colorchannelmixer@{fn}','aa']]]
            },
        ],
    },
    {
        "name": "OverlayWithDelay",
        "timelineSupport":True,
        "filter": "setpts=PTS+{bg_start_Trim}/TB[vin{fn}],movie='{source}':loop=1:seek_point={seek_point},setpts=PTS+{overlay_start_Trim}/TB,scale={w}:{h},rotate=a={angle}:out_w=rotw({angle}):out_h=roth({angle}):fillcolor=none,format=argb,colorchannelmixer=aa={alpha}[pwm{fn}],[vin{fn}][pwm{fn}]overlay=x={x}:y={y}",
        "filterPreview": "setpts=PTS+{bg_start_Trim}/TB[vin{fn}],movie='{source}':seek_point={seek_point},setpts=PTS+{overlay_start_Trim}/TB,scale={w}:{h},rotate=a={angle}:out_w=rotw({angle}):out_h=roth({angle}):fillcolor=none,format=argb,colorchannelmixer=aa={alpha}[pwm{fn}],[vin{fn}][pwm{fn}]overlay=x={x}:y={y}",
        "params": [
            {"n": "source", "d": "resources/logo.png", "type": "file", "fileCategory":"image"},
            {
                "n": "x",
                "d": 5,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 5,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": -1,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": -1,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            },
            {
                "n": "angle",
                "d": 0.0,
                "type": "float",
                "range": [-6.28319, 6.28319],
                "inc": 0.0174533,
            },
            {
                "n": "bg_start_Trim",
                "d": 0.0,
                "type": "float",
                "range": [None, None],
                "inc": 0.01,
            },
            {
                "n": "overlay_start_Trim",
                "d": 0.0,
                "type": "float",
                "range": [None, None],
                "inc": 0.01,
            },
            {
                "n": "seek_point",
                "d": 0.0,
                "type": "float",
                "range": [None, None],
                "inc": 0.01,
            },

            {
                "n": "alpha",
                "d": 1.0,
                "type": "float",
                "range": [0.0, 1.0],
                "inc": 0.01,
            },
        ],
    },
    {
        "name": "OverlayBlend",
        "timelineSupport":True,
        "filter": "null[vin{fn}],movie='{source}':loop=1,scale={w}:{h},format=gbrp[pwm{fn}],color=d=1:s=2x2:c={padcolor}[colourbg{fn}],[colourbg{fn}][vin{fn}]scale2ref=sws_flags=neighbor[colourbgscale{fn}][vinscale{fn}],[colourbgscale{fn}][pwm{fn}]overlay=x={x}:y={y},format=gbrp[pwmscale{fn}],[vinscale{fn}]format=gbrp[vingbrp{fn}],[vingbrp{fn}][pwmscale{fn}]blend=all_mode={blendMode}:all_opacity={all_opacity}",
        "filterPreview": "null[vin{fn}],movie='{source}',scale={w}:{h},format=gbrp[pwm{fn}],color=d=1:s=2x2:c={padcolor}[colourbg{fn}],[colourbg{fn}][vin{fn}]scale2ref=sws_flags=neighbor[colourbgscale{fn}][vinscale{fn}],[colourbgscale{fn}][pwm{fn}]overlay=x={x}:y={y},format=gbrp[pwmscale{fn}],[vinscale{fn}]format=gbrp[vingbrp{fn}],[vingbrp{fn}][pwmscale{fn}]blend=all_mode={blendMode}:all_opacity={all_opacity}",
        "params": [
            {"n": "source", "d": "resources/logo.png", "type": "file", "fileCategory":"image"},
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "all_opacity",
                "d": 1,
                "type": "float",
                "range": [0,1],
                "inc": 0.1,
            },
            {
                "n": "blendMode",
                "d": "addition",
                "type": "cycle",
                "cycle": [
                  "addition",
                  "grainmerge",
                  "and",
                  "average",
                  "burn",
                  "darken",
                  "difference",
                  "grainextract",
                  "divide",
                  "dodge",
                  "freeze",
                  "exclusion",
                  "extremity",
                  "glow",
                  "hardlight",
                  "hardmix",
                  "heat",
                  "lighten",
                  "linearlight",
                  "multiply",
                  "multiply128",
                  "negation",
                  "normal",
                  "or",
                  "overlay",
                  "phoenix",
                  "pinlight",
                  "reflect",
                  "screen",
                  "softlight",
                  "subtract",
                  "vividlight",
                  "xor"
                ],
            },
            {
                "n": "padcolor",
                "d": "Black",
                "type": "cycle",
                "cycle": colours,
            },
            {
                "n": "w",
                "d": -1,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": -1,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            },
        ],
    },


    {
        "name": "Fps",
        "filter": "fps",
        "params": [
            {
                "n": "fps",
                "d": 25,
                "type": "int",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            }
        ],
    },
    
    


    {
        "name": "Scale",
        "category":'Resizing and Cropping',
        "filter": "scale",
        "params": [
            {
                "n": "h",
                "d": 3000,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 10,
            },
            {
                "n": "w",
                "d": 1280,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 10,
            },
            {
                "n": "force_original_aspect_ratio",
                "d": "disable",
                "type": "cycle",
                "cycle": ["disable", "decrease", "increase",],
            },
        ],
    },
    
    
    {
        "name": "tonemap",
        "filter": "zscale=transfer=linear,tonemap={mapping}:param={param}:desat={desat},zscale=transfer=bt709,format=yuv420p",
        "params": [
            {
                "n": "mapping",
                "d": "mobius",
                "type": "cycle",
                "cycle": [
                    "none",
                    "clip",
                    "linear",
                    "gamma",
                    "reinhard",
                    "hable",
                    "mobius",
                ],
            },
            {"n": "param", "d": 0.3, "type": "float", "inc": 0.01},
            {"n": "desat", "d": 2.0, "type": "float", "inc": 0.01},
        ],
    },
    
    {
        "name": "curves",
        "filter": "curves",
        "params": [
            {
                "n": "preset",
                "d": "none",
                "type": "cycle",
                "cycle": [
                    "none",
                    "color_negative",
                    "cross_process",
                    "darker",
                    "increase_contrast",
                    "lighter",
                    "linear_contrast",
                    "medium_contrast",
                    "negative",
                    "strong_contrast",
                    "vintage",
                ],
            }
        ],
    },
    
    {
        "name": "colorkey",
        "filter": "colorkey",
        "params": [
            {
                "n": "color",
                "d": "Black",
                "type": "cycle",
                "cycle": colours,
            },
            {"n": "similarity", "d": 0.01, "type": "float", "range": None, "inc": 0.01},
            {"n": "blend", "d": 0.0, "type": "float", "range": None, "inc": 0.01},
        ],
    },
    
    {
        "name": "chromashift",
        "filter": "chromashift@{fn}",
        "params": [
            {"n": "cbh", "d": 0.0, "type": "float", "range": None, "inc": 0.5,"commandVar":['Chroma-Blue-horiz',[['chromashift@{fn}','cbh']]]},
            {"n": "cbv", "d": 0.0, "type": "float", "range": None, "inc": 0.5,"commandVar":['Chroma-Blue-vert',[['chromashift@{fn}','cbv']]]},
            {"n": "crh", "d": 0.0, "type": "float", "range": None, "inc": 0.5,"commandVar":['Chroma-rh',[['chromashift@{fn}','crh']]]},
            {"n": "crv", "d": 0.0, "type": "float", "range": None, "inc": 0.5,"commandVar":['Chroma-rv',[['chromashift@{fn}','crv']]]},
        ],
    },
    
    {
        "name": "addroi",
        "timelineSupport":True,
        "filter": "addroi=x='{xf}*iw':y={yf}*ih:w={wf}*iw:h={hf}*ih:qoffset={qoffset}",
        "filterPreview": "drawbox=color='Blue@0.25':x='{xf}*iw+({qoffset}*0)':y={yf}*ih:w={wf}*iw:h={hf}*ih:t=fill",
        "encodingStageFilter":True,
        "params": [
            {
                "n": "xf",
                "d": 0,
                "type": "float",
                "range": [0, 1],
                "rectProp": "xf",
                "inc": 0.01,
            },
            {
                "n": "yf",
                "d": 0,
                "type": "float",
                "range": [0, 1],
                "rectProp": "yf",
                "inc": 0.01,
            },
            {
                "n": "wf",
                "d": 0.1,
                "type": "float",
                "range": [0, 1],
                "rectProp": "wf",
                "inc": 0.01,
            },
            {
                "n": "hf",
                "d": 0.1,
                "type": "float",
                "range": [0, 1],
                "rectProp": "hf",
                "inc": 0.01,
            },
            {"n": "qoffset", "d": -0.5, "type": "float", "range": [-1.0, 1.0], "inc": 0.01},
        ],
        "postScale": True,
    },
    
    {
        "name": "lenscorrection",
        "filter": "format=gbrp,lenscorrection@{fn}=cx={cx}:cy={cy}:k1={k1}:k2={k2},format=yuv420p",
        "params": [
            {
                "n": "cx",
                "d": 0.5,
                "type": "float",
                "range": None,
                "rectProp": "xc",
                "inc": 0.01,
            },
            {
                "n": "cy",
                "d": 0.5,
                "type": "float",
                "range": None,
                "rectProp": "yc",
                "inc": 0.01,
            },
            {"n": "k1", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['Lens-K1',[['lenscorrection@{fn}','k1']]]},
            {"n": "k2", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['Lens-K2',[['lenscorrection@{fn}','k2']]]},
        ],
    },
    
    {
        "name": "colorbalance",
        "filter": "colorbalance@{fn}",
        "params": [
            {"n": "rs", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-rs',[['chromashift@{fn}','rs']]]},
            {"n": "gs", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-gs',[['chromashift@{fn}','gs']]]},
            {"n": "bs", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-bs',[['chromashift@{fn}','bs']]]},
            {"n": "rm", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-rm',[['chromashift@{fn}','rm']]]},
            {"n": "gm", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-gm',[['chromashift@{fn}','gm']]]},
            {"n": "bm", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-bm',[['chromashift@{fn}','bm']]]},
            {"n": "rh", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-rh',[['chromashift@{fn}','rh']]]},
            {"n": "gh", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-gh',[['chromashift@{fn}','gh']]]},
            {"n": "bh", "d": 0, "type": "float", "range": None, "inc": 0.01,"commandVar":['ColorBal-bh',[['chromashift@{fn}','bh']]] },
        ],
    },
    
    {
        "name": "unsharp",
        "filter": "unsharp",
        "params": [
            {
                "n": "lx",
                "d": 5,
                "type": "int",
                "range": None,
                "controlGroup": "Position",
                "controlGroupAxis": "x",
                "inc": 1,
            },
            {
                "n": "ly",
                "d": 5,
                "type": "int",
                "range": None,
                "controlGroup": "Position",
                "controlGroupAxis": "y",
                "inc": 1,
            },
        ],
    },
    
    {
        "name": "delogo",
        "timelineSupport":True,
        "filter": "delogo",
        "filterPreview": "delogo=show=1:x={x}:y={y}:w={w}:h={h}",
        "params": [
            {
                "n": "x",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "x",
                "inc": 1
            },
            {
                "n": "y",
                "d": 0,
                "type": "float",
                "range": None,
                "rectProp": "y",
                "inc": 1
            },
            {
                "n": "w",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "w",
                "inc": 1
            },
            {
                "n": "h",
                "d": 100,
                "type": "float",
                "range": None,
                "rectProp": "h",
                "inc": 1
            },
        ],
    },
  
    
    {
        "name": "greyedge",
        "filter": "greyedge",
        "params": [
            {"n": "difford", "d": 1,  "type": "float", "range": [0, 2], "inc": 0.1},
            {"n": "minknorm", "d": 5, "type": "float", "range": [0, 20], "inc": 0.1},
            {"n": "sigma", "d": 2,    "type": "float", "range": [0, 1024.0], "inc": 5},
        ],
    },
    
    {
        "name": "rainbow",
        "filter": "hue='H=2*PI*t*{speed}:s=2'",
        "params": [
            {"n": "speed", "d": 1, "type": "float", "range": [0, 180], "inc": 0.1},
        ],
    },
    
    {
        "name": "rotate",
        "timelineSupport":True,
        "filter": "rotate@{fn}=a={a}:out_w=rotw({a}):out_h=roth({a})",
        "params": [
            {
                "n": "a",
                "d": 0.0,
                "type": "float",
                "range": [-6.28319, 6.28319],
                "inc": 0.0174533,
                "videoSpaceAxis":"deg",
                "videoSpaceSign":1,
                "commandVar":['Rotation',[['rotate@{fn}','a']]]
            },
        ],
    },
    
    {
        "name": "xbr",
        "filter": "xbr",
        "params": [{"n": "n", "d": "2", "type": "cycle", "cycle": [2, 3, 4]}],
    },
    
    {
        "name": "Spin",
        "filter": "rotate=a=t*{speed}",
        "params": [
            {"n": "speed", "d": 1, "type": "float", "range": [0, 180], "inc": 0.1},
        ],
    },
    
    {
        "name": "hue",
        "filter": "hue@{fn}",
        "params": [
            {"n": "h", "d": 0, "type": "float", "range": [0, 360], "inc": 1, "commandVar":['Hue',[['hue@{fn}','h']]] },
            {"n": "s", "d": 2, "type": "float", "range": [-10, 10], "inc": 0.2,      "commandVar":['Saturation',[['hue@{fn}','s']]]},
            {"n": "b", "d": 0, "type": "float", "range": [-10, 10], "inc": 0.2,      "commandVar":['Brightness',[['hue@{fn}','b']]]},
        ],
    },
    
    {"name": "hflip", "filter": "hflip"},
    
    {"name": "vflip", "filter": "vflip"},
    
    {
        "name": "transpose",
        "filter": "transpose",

        "params": [
            {
                "n": "dir",
                "d": "cclock",
                "type": "cycle",
                "cycle": ["cclock_flip", "clock", "cclock", "clock_flip"],
            }
        ],
    },
    
    {
        "name": "yadif",
        "filter": "yadif",
        "params": [
            {
                "n": "mode",
                "d": "send_frame",
                "type": "cycle",
                "cycle": [
                    "send_frame",
                    "send_field",
                    "send_frame_nospatial",
                    "send_field_nospatial",
                ],
            },
            {
                "n": "parity",
                "d": "auto",
                "type": "cycle",
                "cycle": ["tff", "bff", "auto"],
            },
            {"n": "deint", "d": "all", "type": "cycle", "cycle": ["all", "interlaced"]},
        ],
    },
    
    {
        "name": "deblock",
        "filter": "deblock",
        "params": [
            {
                "n": "filter",
                "d": "strong",
                "type": "cycle",
                "cycle": ["weak ", "strong",],
            },
            {"n": "block", "d": 8, "type": "int", "range": None, "inc": 1},
            {"n": "alpha", "d": 0.098, "type": "float", "range": [0, 1], "inc": 0.01},
            {"n": "beta", "d": 0.05, "type": "float", "range": [0, 1], "inc": 0.01},
            {"n": "gamma", "d": 0.05, "type": "float", "range": [0, 1], "inc": 0.01},
            {"n": "delta", "d": 0.05, "type": "float", "range": [0, 1], "inc": 0.01},
        ],
    },
    
    {
        "name": "deshake",
        "filter": "deshake",
        "params": [
            {
                "n": "x",
                "d": -1,
                "type": "int",
                "range": None,
                "rectProp": "x",
                "inc": 1,
            },
            {
                "n": "y",
                "d": -1,
                "type": "int",
                "range": None,
                "rectProp": "y",
                "inc": 1,
            },
            {
                "n": "w",
                "d": -1,
                "type": "int",
                "range": None,
                "rectProp": "w",
                "inc": 1,
            },
            {
                "n": "h",
                "d": -1,
                "type": "int",
                "range": None,
                "rectProp": "h",
                "inc": 1,
            },
            {
                "n": "rx",
                "d": 16,
                "type": "int",
                "range": None,
                "controlGroup": "Size",
                "controlGroupAxis": "x",
                "inc": 1,
            },
            {
                "n": "ry",
                "d": 16,
                "type": "int",
                "range": None,
                "controlGroup": "Size",
                "controlGroupAxis": "y",
                "inc": 1,
            },
            {
                "n": "edge",
                "d": "mirror",
                "type": "cycle",
                "cycle": ["blank", "original", "clamp", "mirror",],
            },
            {"n": "blocksize", "d": 8, "type": "int", "range": None, "inc": 1},
            {"n": "contrast", "d": 125, "type": "int", "range": None, "inc": 1},
            {
                "n": "search",
                "d": "exhaustive",
                "type": "cycle",
                "cycle": ["exhaustive", "less"],
            },
        ],
    },
    



    {
        "name": "loop",
        "filter": "loop",
         "params": [
            {
                "n": "loop",
                "d": -1,
                "type": "int",
                "range": None,
                "inc": 1,
            },
            {
                "n": "size",
                "d": 0,
                "type": "int",
                "range": None,
                "inc": 1,
            },
            {
                "n": "start",
                "d": 0,
                "type": "int",
                "range": None,
                "inc": 1,
            },
          ]
    },

    {
        "name": "drawtext",
        "timelineSupport":True,
        "timelineReinit":True,
        "filter": "drawtext@{fn}",
        "params": [
            {"n": "text", "d": "Text", "type": "string"},
            {"n": "fontfile", "d": "resources/quicksand.otf", "type": "file", "fileCategory":"font"},
            {"n": "x", "d": 1, "type": "int", "range": None, "rectProp": "x", "inc": 1, "_commandVar":['Text-X',[['drawtext@{fn}','x']]] },
            {"n": "y", "d": 1, "type": "int", "range": None, "rectProp": "y", "inc": 1, "_commandVar":['Text-Y',[['drawtext@{fn}','y']]]},
            {
                "n": "borderw",
                "d": 1,
                "type": "int",
                "range": None,

                "inc": 1,
            },
            {
                "n": "boxborderw",
                "d": 1,
                "type": "int",
                "range": None,

                "inc": 1,
            },
            {"n": "box", "d": "0", "type": "cycle", "cycle": [0, 1]},
            {
                "n": "fontcolor",
                "d": "White",
                "type": "cycle",
                "cycle": colours,
            },
            {
                "n": "boxcolor",
                "d": "Pink",
                "type": "cycle",
                "cycle": colours,
            },
            {
                "n": "bordercolor",
                "d": "black",
                "type": "cycle",
                "cycle": colours,
            },
            {"n": "fontsize", "d": 16, "type": "int", "rectProp": "h", "range": None, "inc": 1, "_commandVar":['Text-size',[['drawtext@{fn}','fontsize']]] },
            {"n": "alpha", "d": 1, "type": "float", "range": None, "inc": 0.1, "_commandVar":['Text-size',[['drawtext@{fn}','alpha']]] },
        ],
    },





]

if __name__ == "__main__":
    import webmGenerator