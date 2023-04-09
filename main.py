import numpy as np
import colorsys
import os

# Y is up

##### CONFIG #####
voxel_count = 8

voxel_material = 1

## voxel placement config for pygame ##
window_size = 832 # window_size must be divisible by voxel_count without remainder

grid_col = (200,) * 3

#######################################


debug = True
##################

voxel_max_idx = voxel_count - 1


# array of voxels
if "map.npy" in os.listdir():
    map = np.load("map.npy")
    print("loaded map from map.npy file")

    if map.shape[0] > voxel_count:
        print("map in file is bigger than voxel_count, cropping map")
        map = map[:voxel_count, :voxel_count, :voxel_count]

    elif map.shape[0] < voxel_count:
        print("map in file is smaller than voxel_count, extending map with air")
        count_excess = voxel_count - map.shape[0]
        map = np.pad(map, ((0, count_excess), (0, count_excess), (0, count_excess)), "constant", constant_values=0)

else:
    map = np.zeros((voxel_count, voxel_count, voxel_count), dtype=np.int8)
    print("map.npy not found, creating new map")



# cuboids generated from map using greedy voxel merging
# format: [x1, y1, z1, x2, y2, z2, material]
cuboids = []



print(
"""
    1 - change voxels
    2 - render only voxels (very laggy because of matplotlib)
    3 - greedy voxel merging, rendering only cuboids (verry buggy because of matplotlib)
""")

try:
    mode = int(input(">"))
except ValueError:
    raise ValueError("invalid input. Must be number 1-3")


# pixel material colors
material_cols = tuple(tuple(val for val in colorsys.hsv_to_rgb(h/360, 0.5, 1)) for h in range(0, 360, 36))


################# greedy merging function is here ! #######################
# \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ \/ #

def greedy_voxel_merging():
    map_copy = map.copy()

    for y in range(voxel_count):

        for z in range(voxel_count):

            last_material = 0

            for x in range(voxel_count):

                #### block starting/ending detections ####

                block_ended = False

                # if material changed
                if map_copy[z][y][x] != last_material:
                    ## if block ended
                    # material switch NOT from air
                    if last_material != 0:
                        block_end_x = x
                        block_ended = True

                    # if new block just started AND NOT block ended while new one starting
                    if map_copy[z][y][x] != 0 and not block_ended:
                        block_start_x = x

                ## if block ended
                # end of map row on NOT air
                if x == voxel_max_idx and map_copy[z][y][x] != 0:
                    block_end_x = x + 1
                    block_ended = True
                    last_material = map_copy[z][y][x]

                ############################################

                if block_ended:

                    # scanning for other rows under existing row that can be included in the block
                    block_end_z = z
                    invalid_row = False
                    while True:
                        block_end_z += 1

                        # if the end of the map is reached, break the loop
                        if block_end_z == voxel_count:
                            break

                        # check if all materials in row are the same as the block's material
                        for x2 in range(block_start_x, block_end_x):

                            if map_copy[block_end_z][y][x2] != last_material:
                                invalid_row = True
                                break

                        if invalid_row:
                            break
                        # "else continue"

                        # set all values of next row that will be added to the block to 0 to prevent them from being treeated as a new block in the next z loop iteration
                        map_copy[block_end_z][y][block_start_x:block_end_x] = 0

                    # x, z sizes have been found. now check the size of the y axis
                    block_end_y = y
                    invalid_plane = False
                    while True:
                        block_end_y += 1

                        # if the end of the map is reached, break the loop
                        if block_end_y == voxel_count:
                            break

                        # check if all materials in a "plane" under the current block are the same as the block's material
                        for z2 in range(z, block_end_z):
                            for x2 in range(block_start_x, block_end_x):

                                if map_copy[z2][block_end_y][x2] != last_material:
                                    invalid_plane = True
                                    break

                        if invalid_plane:
                            break
                        # "else continue"

                        # set all values of next plane that will be added to the block to 0 to prevent them from being treeated as a new block in the next y loop iteration
                        map_copy[z:block_end_z, block_end_y, block_start_x:block_end_x] = 0

                    # add block to cuboids list
                    cuboids.append([block_start_x, y, z, block_end_x, block_end_y, block_end_z, last_material - 1])

                    # if last block is touching current block, use current position as current block's start position
                    if map_copy[z][y][x] != 0:
                        block_start_x = x

                last_material = map_copy[z][y][x]



if mode == 1: # place/remove voxels
    import pygame

    #multiply every color value of pixel material colors by 255
    material_cols = tuple(tuple(int(val * 255) for val in color) for color in material_cols)

    pixel_size = window_size // voxel_count
    half_pixel_size = pixel_size / 2

    # pygame init
    pygame.init()
    window = pygame.display.set_mode((window_size, window_size))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 25)

    last_mouse_tile_pos = None
    mouse_pressed = False
    key_pressed = False

    map_slice = voxel_max_idx

    # main loop
    while True:
        # events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # get key presses for 1-9,0 (0 is 10) for material selection
        keys = pygame.key.get_pressed()
        for i in range(10):
            if keys[pygame.K_0 + i]:
                voxel_material = 10 if i == 0 else i

        # get key presses for down/up arrow for map slice change
        if keys[pygame.K_DOWN]:
            if map_slice != 0 and not key_pressed:
                map_slice -= 1
                key_pressed = True

        elif keys[pygame.K_UP]:
            if map_slice != voxel_max_idx and not key_pressed:
                map_slice += 1
                key_pressed = True

        else:
            key_pressed = False


        # pixel placement
        if pygame.mouse.get_pressed()[0]:
            mouse_pos = pygame.mouse.get_pos()

            mouse_tile_pos = (mouse_pos[0] // pixel_size, mouse_pos[1] // pixel_size)

            if not mouse_pressed:
                mouse_place_material = voxel_material if map[mouse_tile_pos[1]][map_slice][mouse_tile_pos[0]] == 0 else 0
                mouse_pressed = True
            

            if last_mouse_tile_pos != mouse_tile_pos:
                map[mouse_tile_pos[1]][map_slice][mouse_tile_pos[0]] = mouse_place_material


            last_mouse_tile_pos = mouse_tile_pos
        elif mouse_pressed:
            mouse_pressed = False
            last_mouse_tile_pos = None

            # save map array to file
            np.save("map.npy", map)
            print("map saved")


        window.fill((0, 0, 0))

        # draw grid lines
        for i in range(voxel_count):
            pygame.draw.line(window, grid_col, (0, i * pixel_size), (window_size, i * pixel_size))
            pygame.draw.line(window, grid_col, (i * pixel_size, 0), (i * pixel_size, window_size))

        # draw all pixels:
        for y in range(voxel_count):
            for x in range(voxel_count):
                if map[y][map_slice][x] != 0:
                    pygame.draw.rect(window, material_cols[map[y][map_slice][x] - 1], (x * pixel_size, y * pixel_size, pixel_size, pixel_size))

        # draw pixel type text
        text = font.render(f"material: {voxel_material}", True, material_cols[voxel_material - 1])
        window.blit(text, (10, 5))

        # draw map slice text
        text = font.render(f"map slice: {map_slice}", True, (255, 255, 255))
        window.blit(text, (10, 30))

        # update
        pygame.display.update()
        clock.tick(60)


elif mode == 2: # render only voxels

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    # Create figure
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.set_xlabel("X")
    ax.set_ylabel("Z")
    ax.set_zlabel("Y")

    ax.set_xlim(voxel_count, 0)
    ax.set_ylim(0, voxel_count)
    ax.set_zlim(0, voxel_count)

    # plot all voxels
    for z in range(voxel_count):
        for y in range(voxel_count):
            for x in range(voxel_count):
                if map[z][y][x] != 0:
                    ax.bar3d(x, z, y, 1, 1, 1, color = material_cols[map[z][y][x] - 1], alpha = 0.5, edgecolor="black")

    plt.show()


elif mode == 3: # greedy voxel merging, rendering only cuboids

    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')


    ax.set_xlabel("X")
    ax.set_ylabel("Z")
    ax.set_zlabel("Y")

    ax.set_xlim(voxel_count, 0)
    ax.set_ylim(0, voxel_count)
    ax.set_zlim(0, voxel_count)

    greedy_voxel_merging()

    # draw all cuboids
    for cuboid in cuboids:
        ax.bar3d(
            cuboid[0], # x
            cuboid[2], # z
            cuboid[1], # y
            cuboid[3] - cuboid[0], # dx
            cuboid[5] - cuboid[2], # dz
            cuboid[4] - cuboid[1], # dy
            color = material_cols[cuboid[6]],
            edgecolor = "black"
        )
    

    plt.show()