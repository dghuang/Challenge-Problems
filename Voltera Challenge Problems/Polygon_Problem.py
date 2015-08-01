from math import fabs, pi
from cmath import sin
TOLERANCE = 1*10**(-10)

class Point:  
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Polygon:
#class polygon is defined by a line that connects several points in a point list
#note: this will return if a point is inside the polygon, not right on the line of the polygon
    def __init__(self):
        self.point_list = []
    #uses ray casting algorithm: if a point is in polygon, it will intersect the sides an odd number of times
    #otherwise, will intersect an even number of times (0 being an even number)
    def intersect(self, point1, point2, point):
        #in this program, the arbitrary line will be a horizontal line going to the right from the point
        #if the line between two points is vertical 
        if fabs(point1.x - point2.x) < TOLERANCE and point1.x > point.x and ((point.y > point2.y and point.y < point1.y) or (point.y > point1.y and point.y < point2.y)):
            return 1
        #if the line between two points is horizontal, we skip it
        elif fabs(point1.y - point2.y) < TOLERANCE and fabs(point1.y - point.y) < TOLERANCE and ((point.x > point1.x and point.x < point2.x) or (point.x > point2.x and point.x < point1.x)):
            return 1
        #extrapolate the slope based on point1 and point2, then see if a horizontal line from y intersects this
        else:
            if point.y < point1.y and point.y > point2.y and point2.x + (point1.x-point2.x)/(point1.y-point2.y)*(point.y-point2.y) > point.x:
                return 1
            elif point.y < point2.y and point.y > point1.y and point1.x + (point2.x-point1.x)/(point2.y-point1.y)*(point.y-point1.y) > point.x:
                return 1
            else:
                return 0
        
    def pointInPolygon(self, point):
        #must have at least three sides to be a polygon
        side = 0
        intersections = 0
        if len(self.point_list) >= 3:
            #iterates over every line between two points, and if the arbitrary point is between the y coordinates and the x coordinate is to the right
            #of the arbitrary point then the arbitrary line crosses through this line
            while side < len(self.point_list)-1:
                intersections += self.intersect(self.point_list[side], self.point_list[side+1], point)
                side += 1
            #must iterate one more time, with the two points being the point at the beginning and end of point_list
            intersections += self.intersect(self.point_list[len(self.point_list)-1], self.point_list[0], point)
        else:
            return False
        if intersections % 2 == 1:
            return True
        else:
            return False
#there would be several ways to test the edge cases of this
#if a "polygon" were added in where several lines intersected each other (ie. not a real polygon), then this would simply return how many times
#a straight line from the the point intersects with the polygon's lines
#if the point is exactly on a line, then this should return False because of python not being able to equate floats, therefore it has to be less than the line to be considered on the line

class RegularOctogon(Polygon):
#class Octogon is also defined by a point list containing each of the eight points
#class Octogon contains two extra variables: starting_point, assuming that it's the top left point and side length
    #if you choose to redefine the dimensions of the polygon, this will recreate the point_list    
    def define_octogon(self):
        del self.point_list[:]
        length = self.length
        x = self.starting_point.x
        y = self.starting_point.y
        self.point_list.append(Point(x, y))
        x += length
        self.point_list.append(Point(x, y))
        y -= length * 2**.5 /2
        x += length * 2**.5 /2
        self.point_list.append(Point(x, y))
        y -= length * 2**.5 /2
        self.point_list.append(Point(x, y))
        y -= length * 2**.5 /2
        x -= length * 2**.5 /2
        self.point_list.append(Point(x, y))
        x -= length * 2**.5 /2
        self.point_list.append(Point(x, y))
        x -= length * 2**.5 /2
        y += length * 2**.5 /2
        self.point_list.append(Point(x, y))
        y += length * 2**.5 /2
        self.point_list.append(Point(x, y))
    
    #class Octogon can be initiated by stating the first point (assuming first point is top left point in octogon) and the Length
    def __init__(self, point, length):
        self.starting_point = point
        self.length = length
        self.define_octogon()