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


    def __str__(self):
        return "[x={}, y={}]".format(self._x, self._y)



class Size:

    def __init__(self, w, h):
        self._w = w
        self._h = h


    @property
    def width(self):
        return self._w


    @property
    def height(self):
        return self._h


    def __str__(self):
        return "[w={}, h={}]".format(self._w, self._h)



class Rect:

    def __init__(self, origin=None, center=None, size=None):
        if size is None:
            raise ValueError()
        if origin is None and center is None:
            raise ValueError()
        if origin is not None and center is not None:
            raise ValueError()

        if origin is not None:
            self._x = origin.x
            self._y = origin.y
        else:
            self._x = center.x - size.width / 2
            self._y = center.y - size.height / 2

        self._w = size.width
        self._h = size.height


    @property
    def width(self):
        return self._w


    @property
    def height(self):
        return self._h


    @property
    def size(self):
        return Size(self.width, self.height)


    @property
    def origin(self):
        return Point(self._x, self._y)


    @property
    def min_x(self):
        return self.origin.x


    @property
    def min_y(self):
        return self.origin.y


    @property
    def max_x(self):
        return self.min_x + self.width


    @property
    def max_y(self):
        return self.min_y + self.height


    @property
    def mid_x(self):
        return self.min_x + self.width / 2


    @property
    def mid_y(self):
        return self.min_y + self.height / 2


    @property
    def top_left(self):
        return Point(self.min_x, self.min_y)


    @property
    def center_left(self):
        return Point(self.min_x, self.mid_y)


    @property
    def bottom_left(self):
        return Point(self.min_x, self.max_y)


    @property
    def top_right(self):
        return Point(self.max_x, self.min_y)


    @property
    def center_right(self):
        return Point(self.max_x, self.mid_y)


    @property
    def bottom_right(self):
        return Point(self.max_x, self.max_y)


    @property
    def center_top(self):
        return Point(self.mid_x, self.min_y)


    @property
    def center(self):
        return Point(self.mid_x, self.mid_y)


    @property
    def center_bottom(self):
        return Point(self.mid_x, self.max_y)


    def inset_by(self, dx, dy):
        return Rect(
            center = self.center,
            size = Size(self.width - 2 * dx, self.height - 2 * dy))


    def __str__(self):
        return "[{}, {}]".format(self.origin, self.size)
