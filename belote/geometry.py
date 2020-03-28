#
# Copyright (C) Florian Denis - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited.
# Proprietary and confidential.
#

class Point:

    def __init__(self, x, y):
        self._x = x
        self._y = y


    @property
    def x(self):
        return self._x


    @property
    def y(self):
        return self._y


    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)


class Size:

    def __init__(self, w, h):
        self._w = w
        self._h = h


    @property
    def w(self):
        return self._w


    @property
    def h(self):
        return self._h



class Rect:

    def __init__(self, origin, size):
        self._x = origin.x
        self._y = origin.y
        self._w = size.w
        self._h = size.h

    @property
    def origin(self):
        return Point(self._x, self._y)


    @property
    def size(self):
        return Size(self._w, self._h)


    @property
    def minX(self):
        return self.origin.x


    @property
    def minY(self):
        return self.origin.y

    @property
    def maxX(self):
        return self.origin.x + self.size.w


    @property
    def maxY(self):
        return self.origin.y + self.size.h


    @property
    def midX(self):
        return self.origin.x + self.size.w/2


    @property
    def midY(self):
        return self.origin.y + self.size.h/2


    @property
    def topLeft(self):
        return Point(minX, minY)


    @property
    def centerLeft(self):
        return Point(minX, midY)


    @property
    def bottomLeft(self):
        return Point(minX, maxY)


    @property
    def topRight(self):
        return Point(maxX, minY)


    @property
    def centerRight(self):
        return Point(maxX, midY)


    @property
    def bottomRight(self):
        return Point(maxX, maxY)


    @property
    def centerTop(self):
        return Point(midX, minY)


    @property
    def center(self):
        return Point(midX, midY)


    @property
    def centerBottom(self):
        return Point(midX, maxY)
