
selectableFilters = [
  
  {"name":"normalize",
   "filter":"normalize"},

  {
    "name":"minterpolate","filter":"minterpolate",
    "params":[
      {"n":"fps", "d":60,"type":"float","range":[1,None],'inc':1},
      {"n":"mi_mode", "d":"mci","type":"cycle","cycle":['mci','dup','blend']},
      {"n":"me_mode", "d":"bidir","type":"cycle","cycle":['bidir','bilat']},
      {"n":"me", "d":"esa","type":"cycle","cycle":['esa','bilat','tss','tdls','ntss','fss','ds','']},
      {"n":"mb_size", "d":16,"type":"float","range":[1,None],'inc':1},



    ]
  }, 

  {"name":"libpostproc+temportaldenoiser",
   "filter":"pp=default/tmpnoise|1|2|3"},

  {"name":"libpostproc-deblock+dering+contrast",
   "filter":"pp=hb/vb/dr/al"},

  {
        "name":"v360 - VR Correction",
        "filter":"v360={in_proj}:{out_proj}:in_stereo={in_stereo}:out_stereo={out_stereo}:id_fov={id_fov}:yaw={yaw}:pitch={pitch}:roll={roll}:d_fov={d_fov}:w={w}:h={h}:interp={interp}:in_trans={in_trans}:out_trans={out_trans}:h_flip={h_flip}:ih_flip={ih_flip}:iv_flip={iv_flip}:alpha_mask=1",
        "params":[
          {"n":"in_proj", "d":"hequirect","type":"cycle","cycle":[
              "sg",
              "fisheye",
              "ball",
              "equirect",
              "hequirect",
              "rectilinear",
              "pannini",
              "cylindrical",


            ]
          },



          {"n":"out_proj", "d":"flat","type":"cycle","cycle":[
              "sg",
              "fisheye",
              "ball",
              "flat",
              "rectilinear",
              "pannini",
              "cylindrical",
            ]
          },

          {"n":"in_trans", "d":"0","type":"cycle","cycle":[
              "1","0",
            ]
          },
          {"n":"out_trans", "d":"0","type":"cycle","cycle":[
              "1","0",
            ]
          },

          {"n":"h_flip", "d":"0","type":"cycle","cycle":[
              "1","0",
            ]
          },
          {"n":"ih_flip", "d":"0","type":"cycle","cycle":[
              "1","0",
            ]
          },
          {"n":"iv_flip", "d":"0","type":"cycle","cycle":[
              "1","0",
            ]
          },

          {"n":"in_stereo", "d":"sbs","type":"cycle","cycle":[
              "sbs",
              "2d",
              "tb"
            ]
          },
          {"n":"out_stereo", "d":"2d","type":"cycle","cycle":[
              "sbs",
              "2d",
              "tb"
            ]
          },

          {"n":"w",      "d":800.0,  "type":"float","range":None, 'inc':1},
          {"n":"h",      "d":800.0,  "type":"float","range":None, 'inc':1},

          {"n":"yaw",      "d":0.0,  "type":"float","range":[-90,90], 'inc':1},
          {"n":"pitch",    "d":0.0,  "type":"float","range":[-90,90], 'inc':1},
          {"n":"roll",     "d":0.0,  "type":"float","range":[-180,180], 'inc':1},
          
          {"n":"d_fov",      "d":90.0,  "type":"float","range":[0,180], 'inc':1},
          {"n":"id_fov",      "d":180.0,  "type":"float","range":[0,180], 'inc':1},

          {"n":"interp", "d":"cubic","type":"cycle","cycle":[
              "linear",
              "lagrange9",
              "cubic",
              "spline16",
              "gaussian",
            ]
          },
        ]
      },

  {
    "name":"IOverlay",
    "filter":"null[vin{fn}],movie='{source}'[pwm{fn}],[vin{fn}][pwm{fn}]overlay=x={x}:y={y}",
    "params":[
      {"n":"source", "d":'logo.png',"type":"file"},
      {"n":"x",      "d":5,  "type":"float","range":None, 'rectProp':'x','inc':1},
      {"n":"y",      "d":5,  "type":"float","range":None, 'rectProp':'y','inc':1},
    ]
  },
  {
    "name":"Scale",
    "filter":"scale",
    "params":[
      {"n":"h",      "d":3000,  "type":"float","range":None, 'rectProp':'x','inc':10},
      {"n":"w",      "d":1280,  "type":"float","range":None, 'rectProp':'y','inc':10},
      {"n":"force_original_aspect_ratio", "d":"disable","type":"cycle","cycle":[
        "disable",
        "decrease",
        "increase",
        ]
      },
    ]
  },
  {
    "name":"VOverlay",
    "filter":"null[vin{fn}],movie='{source}',loop=-1:size={frames},setpts=N/FRAME_RATE/TB[pwm{fn}],[vin{fn}][pwm{fn}]overlay=shortest=0:x={x}:y={y}",
    "params":[
      {"n":"source", "d":'footer.png',"type":"file"},
      {"n":"x",      "d":100,  "type":"float","range":None, 'rectProp':'x','inc':1},
      {"n":"y",      "d":100,  "type":"float","range":None, 'rectProp':'y','inc':1},
      {"n":"frames", "d":100,  "type":"float","range":[0,999],'inc':1},
    ]
  },

  {
    "name":"tonemap",
    "filter":"zscale=transfer=linear,tonemap={mapping}:param={param},zscale=transfer=bt709,format=yuv420p",
    "params":[
        {"n":"mapping", "d":"none","type":"cycle","cycle":[
          "none",
          "clip",
          "linear",
          "gamma",
          "reinhard",
          "hable",
          "mobius",
          ]
        },
        {"n":"param", "d":1.0,  "type":"float",'inc':0.01},

      ]
  },


  {
    "name":"curves",
    "filter":"curves",
    "params":[
      {"n":"preset", "d":"none","type":"cycle","cycle":[
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
        ]
      }
    ]
  },

  {
    "name":"colorkey",
    "filter":"colorkey",
    "params":[
      {"n":"color", "d":"Black","type":"cycle","cycle":[
          "Black",
          "Gray",
          "White",
          "Red",
          "Green",
          "Blue",
          "Pink",
          "Thistle",
          "invert"
        ]
      },
      {"n":"similarity",  "d":0.01, "type":"float", "range":None,     'inc':0.01},
      {"n":"blend",       "d":0.0,  "type":"float", "range":None, 'inc':0.01},
    ]
  },



  {
    "name":"chromashift",
    "filter":"chromashift",
    "params":[

      {"n":"cbh",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},
      {"n":"cbv",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},
      {"n":"crh",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},
      {"n":"crv",           "d":0.0,  "type":"float", "range":None, 'inc':0.5},

    ]
  },
  {
    "name":"addroi",
    "filter":"addroi=x='{xf}*iw':y={yf}*ih:w={wf}*iw:h={hf}*ih:qoffset={qoffset}",
    "filterPreview":"drawbox=color=Blue@0.25:x='{xf}*iw+({qoffset}*0)':y={yf}*ih:w={wf}*iw:h={hf}*ih:t=fill",
    "params":[
      {"n":"xf",      "d":0,      "type":"float",  "range":[0,1], 'rectProp':'xf',  'inc':0.01},
      {"n":"yf",      "d":0,      "type":"float",  "range":[0,1], 'rectProp':'yf',  'inc':0.01},
      {"n":"wf",      "d":0.1,    "type":"float",  "range":[0,1], 'rectProp':'wf', 'inc':0.01},
      {"n":"hf",      "d":0.1,    "type":"float",  "range":[0,1], 'rectProp':'hf', 'inc':0.01},
      {"n":"qoffset",  "d":-0.5, "type":"float",   "range":[-1,1], 'inc':0.01},
    ],
    "postScale":True,
  },


    



  {
    "name":"lenscorrection",
    "filter":"format=gbrp,lenscorrection=cx={cx}:cy={cy}:k1={k1}:k2={k2},format=yuv420p",
    "params":[
      {"n":"cx",      "d":0.5,  "type":"float","range":None, 'rectProp':'xc', 'inc':0.01},
      {"n":"cy",      "d":0.5,  "type":"float","range":None, 'rectProp':'yc', 'inc':0.01},
      {"n":"k1",      "d":0,    "type":"float","range":None, 'inc':0.01},
      {"n":"k2",      "d":0,    "type":"float","range":None, 'inc':0.01},
    ]
  },



  {
    "name":"colorbalance",
    "filter":"colorbalance",
    "params":[
      {"n":"rs",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"gs",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"bs",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"rm",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"gm",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"bm",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"rh",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"gh",      "d":0,  "type":"float","range":None, 'inc':0.01},
      {"n":"bh",      "d":0,  "type":"float","range":None, 'inc':0.01},
    ]
  },

  {
    "name":"unsharp",
    "filter":"unsharp",
    "params":[
      {"n":"lx",      "d":5,  "type":"int","range":None, 'controlGroup':'Position', 'controlGroupAxis':'x','inc':1},
      {"n":"ly",      "d":5,  "type":"int","range":None, 'controlGroup':'Position', 'controlGroupAxis':'y','inc':1},
    ]
  },

  {
    "name":"delogo",
    "filter":"delogo",
    "filterPreview":"delogo=show=1:x={x}:y={y}:w={w}:h={h}",
    "params":[
      {"n":"x",      "d":0,  "type":"float","range":None, 'rectProp':'x','inc':1},
      {"n":"y",      "d":0,  "type":"float","range":None, 'rectProp':'y','inc':1},
      {"n":"w",      "d":100,"type":"float","range":None, 'rectProp':'w','inc':1},
      {"n":"h",      "d":100,"type":"float","range":None, 'rectProp':'h','inc':1}
    ]
  },
  {
    "name":"drawbox",
    "filter":"drawbox",
    "params":[
      {"n":"x",      "d":0,  "type":"float","range":None, 'rectProp':'x','inc':1},
      {"n":"y",      "d":0,  "type":"float","range":None, 'rectProp':'y','inc':1},
      {"n":"w",      "d":100,"type":"float","range":None, 'rectProp':'w','inc':1},
      {"n":"h",      "d":100,"type":"float","range":None, 'rectProp':'h','inc':1},
      {"n":"t", "d":"fill","type":"cycle","cycle":[
          "fill",
          "1",
          "2",
          "5",
          "w/3"
          "w/5"
          "w/10"
        ]
      },
      {"n":"color", "d":"Black","type":"cycle","cycle":[
          "Black",
          "Gray",
          "White",
          "Red",
          "Green",
          "Blue",
          "Pink",
          "Thistle",
          "invert"
        ]
      }
    ]
  },
  {
    "name":"greyedge",
    "filter":"greyedge",
    "params":[
      {"n":"difford", "d":1,"type":"float","range":[0,2],'inc':0.1},
      {"n":"minknorm","d":5,"type":"float","range":[0,20],'inc':0.1},
      {"n":"sigma",   "d":2,"type":"float","range":[0,1024.0],'inc':5}
    ]
  },

  {"name":"rainbow","filter":"hue='H=2*PI*t*{speed}:s=2'",
    "params":[
      {"n":"speed", "d":1,"type":"float","range":[0,180],'inc':0.1},
    ]
  },
  {
    "name":"rotate","filter":"rotate",
    "params":[
      {"n":"a", "d":0.785398,"type":"float","range":[0,6.28319],'inc':0.0174533},
    ]
  },

  {
    "name":"xbr","filter":"xbr",
    "params":[
      {"n":"n", "d":"2","type":"cycle","cycle":[2,3,4]}
    ]
  },

  {
    "name":"Spin","filter":"rotate=a=t*{speed}",
    "params":[
      {"n":"speed", "d":1,"type":"float","range":[0,180],'inc':0.1},
    ]
  },
  {
    "name":"hue","filter":"hue",
    "params":[
      {"n":"h", "d":0,"type":"float","range":[0,360],'inc':0.0174533},
      {"n":"s", "d":2,"type":"float","range":[-10,10],'inc':0.2},
      {"n":"b", "d":0,"type":"float","range":[-10,10],'inc':0.2},
    ]
  }, 

  {"name":"hflip","filter":"hflip"},
  {"name":"vflip","filter":"vflip"},

 
  {
    "name":"transpose","filter":"transpose",
    "params":[
      {"n":"dir", "d":"cclock","type":"cycle","cycle":[
          "cclock_flip",
          "clock",
          "cclock",
          "clock_flip"
        ]
      }
    ]
  }, 
  {
    "name":"yadif","filter":"yadif",
    "params":[
      {"n":"mode",  "d":"send_frame","type":"cycle","cycle":[
        'send_frame',
        'send_field',
        'send_frame_nospatial',
        'send_field_nospatial'
        ]
      },
      {"n":"parity","d":"auto","type":"cycle","cycle":[
        'tff',
        'bff',
        'auto'
        ]
      },
      {"n":"deint","d":"all","type":"cycle","cycle":[
        'all',
        'interlaced'
        ]
      }
    ]
  },

  {"name":"deblock","filter":"deblock",
    "params":[
      {"n":"filter","d":"strong","type":"cycle","cycle":[
        'weak ',
        'strong',
        ]
      },
      {"n":"block",      "d":8,  "type":"int","range":None,'inc':1},
      {"n":"alpha", "d":0.098,"type":"float","range":[0,1],'inc':0.01},
      {"n":"beta",  "d":0.05,"type":"float","range":[0,1],'inc':0.01},
      {"n":"gamma", "d":0.05,"type":"float","range":[0,1],'inc':0.01},
      {"n":"delta", "d":0.05,"type":"float","range":[0,1],'inc':0.01},
    ]
  },

  {"name":"deshake","filter":"deshake",
   "params":[
      {"n":"x",      "d":-1,  "type":"int","range":None, 'rectProp':'x','inc':1},
      {"n":"y",      "d":-1,  "type":"int","range":None, 'rectProp':'y','inc':1},
      {"n":"w",      "d":-1,  "type":"int","range":None, 'rectProp':'w','inc':1},
      {"n":"h",      "d":-1,  "type":"int","range":None, 'rectProp':'h','inc':1},

      {"n":"rx",      "d":16,  "type":"int","range":None, 'controlGroup':'Size',     'controlGroupAxis':'x','inc':1},
      {"n":"ry",      "d":16,  "type":"int","range":None, 'controlGroup':'Size',     'controlGroupAxis':'y','inc':1},

      {"n":"edge","d":"mirror","type":"cycle","cycle":[
        'blank',
        'original',
        'clamp',
        'mirror',
        ]
      },

      {"n":"blocksize",      "d":8,  "type":"int","range":None,'inc':1},
      {"n":"contrast",       "d":125,  "type":"int","range":None,'inc':1},
      {"n":"search","d":"exhaustive","type":"cycle","cycle":[
        'exhaustive',
        'less'
        ]
      }



    ]
  },

  {
    "name":"crop",
    "filter":"crop",
    "params":[
      {"n":"x",      "d":0,      "type":"int","range":None, 'rectProp':'x', 'inc':10},
      {"n":"y",      "d":0,      "type":"int","range":None, 'rectProp':'y', 'inc':10},
      {"n":"w",      "d":100,    "type":"int","range":None, 'rectProp':'w', 'inc':10},
      {"n":"h",      "d":100,    "type":"int","range":None, 'rectProp':'h', 'inc':10},
    ]
  },

  {
    "name":"drawtext",
    "filter":"drawtext",
    "params":[
      {"n":"text",    "d":"Text","type":"string"},
      {"n":"fontfile",    "d":"font.ttf","type":"string"},

      {"n":"x",       "d":1,  "type":"int","range":None, 'rectProp':'x','inc':1},
      {"n":"y",       "d":1,  "type":"int","range":None, 'rectProp':'y','inc':1},
    
      {"n":"borderw",       "d":1,  "type":"int","range":None, 'rectProp':'y','inc':1},
      {"n":"boxborderw",       "d":1,  "type":"int","range":None, 'rectProp':'y','inc':1},
      
      {"n":"box", "d":"1","type":"cycle","cycle":[0,1]},
      {"n":"text_shaping", "d":"1","type":"cycle","cycle":[0,1]},



      {"n":"fontcolor", "d":"White","type":"cycle","cycle":[
          "Black",
          "Gray",
          "White",
          "Red",
          "Green",
          "Blue",
          "Pink",
          "Thistle",
          "invert"
        ]
      },

      {"n":"boxcolor", "d":"Pink","type":"cycle","cycle":[
          "Black",
          "Gray",
          "White",
          "Red",
          "Green",
          "Blue",
          "Pink",
          "Thistle",
          "invert"
        ]
      },

      {"n":"bordercolor", "d":"black","type":"cycle","cycle":[
          "Black",
          "Gray",
          "White",
          "Red",
          "Green",
          "Blue",
          "Pink",
          "Thistle",
          "invert"
        ]
      },


      {"n":"fontsize","d":16,  "type":"int","range":None,'inc':1},
      {"n":"alpha",   "d":1,  "type":"float","range":None,'inc':0.1},
    ]
  },


]

if __name__ == '__main__':
  import webmGenerator