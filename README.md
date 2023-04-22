# greedy-voxel-merging-prototype

This one is in 3D!

## Usage
Use keys 0-9 to select material (voxel type) and up/down arrows to change y slice of the map. Use mouse button to place/remove voxels. This applies only in the "change voxels" mode.

## Meshing
Meshing generates a mesh without faces that touch chunk sides or are completely covered with voxels. For simplicity, faces that have at least one air voxel touching them are not removed.