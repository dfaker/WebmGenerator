

from math import floor

class Brick:

  def __init__(self,identifier,width,height):
    self.identifier=identifier
    self.height=height*1.0
    self.width=width*1.0

  def __repr__(self):
    return "<b{} {}x{}>".format(self.identifier,self.width,self.height)

  def getSize(self):
    return self.width,self.height

  def getSizeWithContstraint(self,constrainedDirection,constraint,logger=None,xo=None,yo=None,padding=0):
    if constraint is None:
      if logger is not None:
        logger[self.identifier]=(floor(xo)+padding,
                                 floor(yo)+padding,
                                 floor(self.width)-(padding*2),
                                 floor(self.height)-(padding*2),
                                 1.0,
                                 floor(self.width)-(padding*2),
                                 floor(self.height)-(padding*2))

      return floor(self.width),floor(self.height)
    else:
      if constrainedDirection=='height':
        ar = constraint/self.height
        if logger is not None:
          logger[self.identifier]=(floor(xo)+padding,
                                   floor(yo)+padding,
                                   floor(self.width*ar)-(padding*2),
                                   floor(constraint)-(padding*2),
                                   ar,
                                   floor(self.width)-(padding*2),
                                   floor(self.height)-(padding*2))

        return floor(self.width*ar),floor(constraint)

      elif constrainedDirection=='width':
        ar = constraint/self.width
        if logger is not None:
          logger[self.identifier]=(floor(xo)+padding,
                                   floor(yo)+padding,
                                   floor(constraint)-(padding*2),
                                   floor(self.height*ar)-(padding*2),
                                   ar,
                                   floor(self.width)-(padding*2),
                                   floor(self.height)-(padding*2))
        return floor(constraint),floor(self.height*ar)
      else:
        raise Exception('Invalid direction {}'.format(constrainedDirection))

class Stack:

  def __init__(self,bricks,orientation='vertical'):
    if orientation not in ('vertical','horizontal'):
      raise Exception('Invalid orientation')
    self.bricks=bricks
    self.orientation=orientation

  def __init__(self,bricks,orientation='vertical'):
    if orientation not in ('vertical','horizontal'):
      raise Exception('Invalid orientation')
    self.bricks=bricks
    self.orientation=orientation

  def append(self,brick):
    self.bricks.append(brick)

  def insert(self,pos,brick):
    self.bricks.insert(pos,brick)

  def __repr__(self):
    return "<s{} {}>".format(self.orientation,len(self.bricks))


  def getSizeWithContstraint(self,direction,constraint,logger=None,xo=None,yo=None,padding=0):
    if direction=='height':
      if self.orientation=='vertical':
        heights=[]
        for brick in self.bricks:
          _,h = brick.getSizeWithContstraint('width',1000)
          heights.append(h)
        sumheights=sum(heights)

        finalwidth=0
        finalheight=0
        heights = [(h/sumheights)*constraint for h in heights]
        for requestedHeight,brick in zip(heights,self.bricks):
          w,h = brick.getSizeWithContstraint('height',requestedHeight,logger,xo,None if yo is None else yo+finalheight,padding=padding)
          finalwidth=w
          finalheight+=h

        return floor(finalwidth),floor(finalheight)
      elif self.orientation=='horizontal':
        finalwidth=0
        finalheight=0
        for brick in self.bricks:
          w,h = brick.getSizeWithContstraint('height',constraint,logger,None if xo is None else xo+finalwidth,yo,padding=padding)
          finalwidth+=w
          finalheight=h
        return floor(finalwidth),floor(finalheight)
    elif direction=='width':
      if self.orientation=='horizontal':
        widths=[]
        for brick in self.bricks:
          w,_ = brick.getSizeWithContstraint('height',1000,padding=padding)
          widths.append(w)
        sumwidths=sum(widths)

        finalwidth=0
        finalheight=0
        widths = [(w/sumwidths)*constraint for w in widths]

        for requestedWidth,brick in zip(widths,self.bricks):
          w,h = brick.getSizeWithContstraint('width',requestedWidth,logger,None if xo is None else xo+finalwidth,yo,padding=padding)
          finalwidth+=w
          finalheight=h
        return floor(finalwidth),floor(finalheight)
      elif self.orientation=='vertical':
        finalwidth=0
        finalheight=0
        for brick in self.bricks:
          w,h = brick.getSizeWithContstraint('width',constraint,logger,xo,None if yo is None else yo+finalheight,padding=padding)
          finalwidth=w
          finalheight+=h
        return floor(finalwidth),floor(finalheight)
    else:
      raise Exception('Invalid direction')
