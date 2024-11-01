# Triangulate.py - Python script for triangulating polygons
#
# This script specializes in triangulating polygons using two techniques:
# - Fan method for convex polygons
# - Earcut technique for concave polygons
#
# Adapted to Cython by Benjamin Dittes.
#
# Copyright (c) 2023 by FalconCoding
# Author: Stefan Johnsen
# Email: stefan.johnsen@outlook.com
#
# This software is released under the MIT License.

import cython as cy

epsilon = cy.declare(cy.double, 1e-6)

TurnRight = cy.declare(cy.int, 1)
TurnLeft = cy.declare(cy.int, -1)
TurnNoTurn = cy.declare(cy.int, 0)

Point = cy.struct(x=cy.double, y=cy.double, z=cy.double, i=cy.int)

Triangle = cy.struct(i0=cy.int, i1=cy.int, i2=cy.int)


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def Point_sub(a: Point, b: Point) -> Point:
    return Point(a.x - b.x, a.y - b.y, a.z - b.z, 0)


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def dot(u: Point, v: Point) -> cy.double:
    return u.x * v.x + u.y * v.y + u.z * v.z


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def cross(u: Point, v: Point) -> Point:
    x: cy.double = u.y * v.z - u.z * v.y
    y: cy.double = u.z * v.x - u.x * v.z
    z: cy.double = u.x * v.y - u.y * v.x
    return Point(x, y, z, 0)


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def length(u: Point) -> cy.double:
    return (u.x * u.x + u.y * u.y + u.z * u.z)**0.5


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def turn(p: Point, u: Point, n: Point, q: Point) -> cy.int:
    v: Point = cross(Point_sub(q, p), u)
    d: cy.double = dot(v, n)

    if d > +epsilon:
        return TurnRight
    if d < -epsilon:
        return TurnLeft

    return TurnNoTurn


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def triangleAreaSquared(a: Point, b: Point, c: Point) -> cy.double:
    c: Point = cross(Point_sub(b, a), Point_sub(c, a))
    return length(c)**2.0 / 4.0


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def normalize(v: Point) -> Point:
    vl: cy.double = length(v)
    return Point(v.x / vl, v.y / vl, v.z / vl, 0)


@cy.cfunc
@cy.exceptval(check=False)
def normal(polygon: list[Point]) -> Point:
    n: cy.int = len(polygon)
    v: Point = Point(0, 0, 0, 0)

    if n < 3:
        return v

    index: cy.int = 0
    for index in range(n):
        item: Point = polygon[index % n]
        next: Point = polygon[(index + 1) % n]

        v.x += (next.y - item.y) * (next.z + item.z)
        v.y += (next.z - item.z) * (next.x + item.x)
        v.z += (next.x - item.x) * (next.y + item.y)

    return normalize(v)


@cy.cfunc
@cy.nogil
@cy.exceptval(check=False)
def pointInsideOrEdgeTriangle(a: Point, b: Point, c: Point, p: Point) -> tuple[cy.bint, cy.bint]:
    zero: cy.double = 1e-15  # A small value close to zero for comparisons

    # Initialize edge to False
    edge: cy.bint = False

    # Vectors from point p to vertices of the triangle
    v0 = Point_sub(c, a)
    v1 = Point_sub(b, a)
    v2 = Point_sub(p, a)

    dot00 = dot(v0, v0)
    dot01 = dot(v0, v1)
    dot02 = dot(v0, v2)
    dot11 = dot(v1, v1)
    dot12 = dot(v1, v2)

    # Check for degenerate triangle
    denom = dot00 * dot11 - dot01 * dot01

    if abs(denom) < zero:
        # The triangle is degenerate (i.e., has no area)
        return (False, edge)

    # Compute barycentric coordinates
    invDenom = 1.0 / denom

    u = (dot11 * dot02 - dot01 * dot12) * invDenom
    v = (dot00 * dot12 - dot01 * dot02) * invDenom

    # Check for edge condition
    if abs(u) < zero or abs(v) < zero or abs(u + v - 1) < zero:
        edge = True

    # Check if point is inside the triangle (including edges)
    return (u >= 0.0 and v >= 0.0 and u + v < 1.0, edge)


@cy.cfunc
@cy.exceptval(check=False)
def isEar(index: cy.int, polygon: list[Point], normal: Point) -> cy.bint:
    n = len(polygon)

    if n < 3:
        return False
    if n == 3:
        return True

    prevIndex: cy.int = (index - 1 + n) % n
    itemIndex: cy.int = index % n
    nextIndex: cy.int = (index + 1) % n

    prev: Point = polygon[prevIndex]
    item: Point = polygon[itemIndex]
    next: Point = polygon[nextIndex]

    u = normalize(Point_sub(item, prev))

    if turn(prev, u, normal, next) != TurnRight:
        return False

    i: cy.int = 0
    for i in range(n):
        if i in (prevIndex, itemIndex, nextIndex):
            continue

        p: Point = polygon[i]

        inside, _ = pointInsideOrEdgeTriangle(prev, item, next, p)

        if inside:
            return False

    return True


@cy.cfunc
@cy.exceptval(check=False)
def getBiggestEar(polygon: list[Point], normal: Point):
    n: cy.int = len(polygon)

    if n == 3:
        return 0
    if n == 0:
        return -1

    maxIndex = -1
    maxArea = float("-inf")

    index: cy.int = 0
    for index in range(n):
        if isEar(index, polygon, normal):
            prev: Point = polygon[(index - 1 + n) % n]
            item: Point = polygon[index % n]
            next: Point = polygon[(index + 1) % n]

            area = triangleAreaSquared(prev, item, next)

            if area > maxArea:
                maxIndex = index
                maxArea = area

    return maxIndex


@cy.cfunc
@cy.exceptval(check=False)
def getOverlappingEar(polygon: list[Point], normal: Point):
    n: cy.int = len(polygon)

    if n == 3:
        return 0
    if n == 0:
        return -1

    index: cy.int = 0
    for index in range(n):
        prev: Point = polygon[(index - 1 + n) % n]
        item: Point = polygon[index % n]
        next: Point = polygon[(index + 1) % n]

        u = normalize(Point_sub(item, prev))

        if turn(prev, u, normal, next) != TurnNoTurn:
            continue

        v = normalize(Point_sub(next, item))

        if dot(u, v) < 0.0:
            return index

    return -1


@cy.cfunc
@cy.exceptval(check=False)
def convex(polygon: list[Point], normal: Point):
    n: cy.int = len(polygon)

    if n < 3:
        return False
    if n == 3:
        return True

    polygonTurn = TurnNoTurn

    index: cy.int = 0
    for index in range(n):
        prev: Point = polygon[(index - 1 + n) % n]
        item: Point = polygon[index % n]
        next: Point = polygon[(index + 1) % n]

        u = normalize(Point_sub(item, prev))

        item_turn = turn(prev, u, normal, next)

        if item_turn == TurnNoTurn:
            continue

        if polygonTurn == TurnNoTurn:
            polygonTurn = item_turn

        if polygonTurn != item_turn:
            return False

    return True


@cy.cfunc
@cy.exceptval(check=False)
def clockwiseOriented(polygon: list[Point], normal: Point):
    n: cy.int = len(polygon)

    if n < 3:
        return False

    orientationSum = 0.0

    index: cy.int = 0
    for index in range(n):
        prev: Point = polygon[(index - 1 + n) % n]
        item: Point = polygon[index % n]
        next: Point = polygon[(index + 1) % n]

        edge = Point_sub(item, prev)
        toNextPoint = Point_sub(next, item)

        v = cross(edge, toNextPoint)
        orientationSum += dot(v, normal)

    return orientationSum < 0.0


@cy.cfunc
@cy.exceptval(check=False)
def makeClockwiseOrientation(polygon: list[Point], normal: Point):
    if len(polygon) < 3:
        return

    if not clockwiseOriented(polygon, normal):
        polygon.reverse()


@cy.cfunc
@cy.exceptval(check=False)
def fanTriangulation(polygon: list[Point]):
    triangles = []
    index: cy.int = 0
    a: Point = polygon[0]
    for index in range(1, len(polygon) - 1):
        b: Point = polygon[index]
        c: Point = polygon[index + 1]
        triangles.append(Triangle(a.i, b.i, c.i))
    return triangles


@cy.cfunc
@cy.exceptval(check=False)
def cutTriangulation(polygon: list[Point], normal: Point):

    triangles = []

    makeClockwiseOrientation(polygon, normal)

    while polygon:
        index = getBiggestEar(polygon, normal)

        if index == -1:
            index = getOverlappingEar(polygon, normal)

        if index == -1:
            return []

        n = len(polygon)

        prev: Point = polygon[(index - 1 + n) % n]
        item: Point = polygon[index % n]
        next: Point = polygon[(index + 1) % n]

        triangles.append(Triangle(prev.i, item.i, next.i))

        del polygon[index]

        if len(polygon) < 3:
            break

    return triangles if len(polygon) < 3 else []


def triangulate(pypolygon):

    # polygon = removeConsecutiveEqualPoints(polygon)
    # print(len(polygon))

    polygon = [Point(p[0], p[1], p[2], p[3]) for p in pypolygon]
    n = normal(polygon)

    if len(polygon) < 3:
        return [], n

    ts = []
    if len(polygon) == 3:
        ts = [Triangle(pypolygon[0][3], pypolygon[1][3], pypolygon[2][3])]
    elif convex(polygon, n):
        ts = fanTriangulation(polygon)
    else:
        ts = cutTriangulation(polygon, n)

    t: Triangle
    ret = []
    for t in ts:
        ret.append([t.i0, t.i1, t.i2])
    return ret, n
