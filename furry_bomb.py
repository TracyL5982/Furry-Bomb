import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from math import sqrt, pi, sin, cos, radians, atan2, degrees

# Constants
TAU = 2 * pi
GOLDEN_ANGLE = pi * (3 - sqrt(5))

def getTNBfromVector(v):
    """
    Calculates the Tangent, Normal, and Binormal (T, N, B) vectors from a given vector.
   
    Parameters:
    - v: The input vector from which T, N, and B are calculated.
   
    Returns:
    - T: Tangent vector.
    - N: Normalized input vector (Normal).
    - B: Binormal vector.
    """
    v = Vector(v)
    N = v.normalized()
    B = N.cross((0, 0, -1))
    if B.length == 0:
        B, T = Vector((1, 0, 0)), Vector((0, 1, 0))
    else:
        B.normalize()
        T = N.cross(B).normalized()
    return T, N, B

def draw_lsystem(bm, position, axiom, rules, iterations, angle, distance, rotation_angle):
    """
    Draws an L-system pattern using Blender's bmesh.

    Parameters:
    - bm: The bmesh to which the L-system pattern is added.
    - position: The starting position for drawing the L-system.
    - axiom: The initial string (seed) of the L-system.
    - rules: The transformation rules for each character in the axiom.
    - iterations: The number of iterations to evolve the axiom.
    - angle: The angle for rotation commands in the L-system.
    - distance: The distance to move forward for the 'F' command.
    - rotation_angle: The angle to rotate the entire pattern after drawing.
    """
    current_string = axiom
    for _ in range(iterations):
        next_string = ""
        for char in current_string:
            next_string += rules.get(char, char)
        current_string = next_string

    direction = Vector((0, 1, 0))
    vert_list = []
    for char in current_string:
        if char == 'F':
            next_position = position + direction * distance
            vert = bm.verts.new(next_position)  
            vert_list.append(vert)  
            position = next_position
        elif char == '+':
            direction.rotate(Matrix.Rotation(radians(angle), 4, 'Z'))
        elif char == '-':
            direction.rotate(Matrix.Rotation(-radians(angle), 4, 'Z'))

    if len(vert_list) > 2:
        try:
            bm.faces.new(vert_list)
        except ValueError:
            print("Could not create a face with the given vertices.")

        rotation_matrix = Matrix.Rotation(radians(rotation_angle), 4, position.normalized())

        for vert in vert_list:
            vert.co -= position  
            vert.co = rotation_matrix @ vert.co  
            vert.co += position  

class PhyllotaxisFlower():
    """
    A class for generating phyllotaxis flower patterns in Blender using bmesh.
    """
    def __init__(self, scene):
        # n : the total number of flowers
        # m : the total number of petals in each flower
        self.n, self.m = 200, 10  
        # r0: the radius of the cone base
        # r1: the distance between petals in each flower
        # r2: the size of the petals
        self.r0, self.r1, self.r2 = 10, 10, 1
       
        # h0: the height of the cone
        # h1: the distance of each flower from the center
        self.h0, self.h1 = 50, 2

        mesh = bpy.data.meshes.new('PhyllotaxisFlower')
        self.obj = bpy.data.objects.new('PhyllotaxisFlower', mesh)

        bm = self.geometry()
        bm.to_mesh(mesh)
        mesh.update()
        bm.free()

        scene.collection.objects.link(self.obj)

    def geometry(self):
        """
        Generates the geometry for the phyllotaxis flower pattern.

        Returns:
        - bm: The bmesh containing the generated geometry.
        """
        bm = bmesh.new()
        for i in range(self.n):
            t0 = i / self.n
            r0, theta = t0 * self.r0, i * GOLDEN_ANGLE

            x = r0 * cos(theta)
            y = r0 * sin(theta)
            z = self.h0 / 2 - (self.h0 / (self.r0 * self.r0)) * r0 * r0
            p0 = Vector((x, y, z))

            T0, N0, B0 = getTNBfromVector(p0)
            M0 = Matrix([T0, B0, N0]).to_4x4().transposed()

            for j in range(self.m):
                t1 = j / self.m
                t2 = 0.4 + 0.6 * t0
                r1, theta = t2 * t1 * self.r1, j * GOLDEN_ANGLE

                x = r1 * cos(theta)
                y = r1 * sin(theta)
                z = self.h1 - (self.h1 / (self.r1 * self.r1)) * r1 * r1
                p1 = Vector((x, y, z))
                T1, N1, B1 = getTNBfromVector(p1)
                M1 = Matrix([T1, B1, N1]).to_4x4().transposed()

                p = p0 + (M0 @ p1)

                center_angle = atan2(p.y, p.x)  
                # angle_offset: an offset/adjustment to the rotation angle of each petal
                angle_offset = 45
                rotation_angle = degrees(center_angle) - angle_offset
                draw_lsystem(bm, p, "F++F++F", {"F": "F-F++F-F"}, 4, 60, 0.05, rotation_angle)

        return bm


if __name__ == '__main__':
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    flower = PhyllotaxisFlower(bpy.context.scene)
