# Copyright (c) 2019 fortiss GmbH
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import os
import unittest
import time
import math
import filecmp
import matplotlib.pyplot as plt
from bark.world import World
from bark.geometry import ComputeCenterLine
from bark.world.map import MapInterface
from modules.runtime.commons.parameters import ParameterServer
from modules.runtime.commons.xodr_parser import XodrParser
from modules.runtime.viewer.matplotlib_viewer import MPViewer
from bark.geometry import Point2d, Polygon2d
from bark.world.opendrive import XodrDrivingDirection

import numpy as np
import itertools

# Name and Output Directory
# CHANGE THIS #
map_name = "three_way_plain"
output_dir = "/tmp/" + map_name

# Map Definition
xodr_parser = XodrParser("modules/runtime/tests/data/" + map_name + ".xodr")

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# World Definition
params = ParameterServer()
world = World(params)

map_interface = MapInterface()
map_interface.SetOpenDriveMap(xodr_parser.map)
world.SetMap(map_interface)

open_drive_map = world.map.GetOpenDriveMap()

viewer = MPViewer(params=params,
                  use_world_bounds=True)
viewer.drawWorld(world)
viewer.saveFig(output_dir + "/" + "world_plain.png")

color_triplet_gray = (0.7,0.7,0.7)

# Open Drive Elements (XodrRoads, XodrLane Sections, XodrLanes)
for idx_r, road in open_drive_map.GetRoads().items():
  viewer.drawWorld(world)
  viewer.drawXodrRoad(road)
  viewer.saveFig(output_dir + "/" + "open_drive_map_road_" + str(idx_r) + ".png")
  viewer.show(block=False)
  viewer.clear()

for idx_r, road in open_drive_map.GetRoads().items():
  for idx_ls, lane_section in enumerate(road.lane_sections):
    viewer.drawWorld(world)
    viewer.drawXodrRoad(road, color_triplet_gray)
    viewer.drawXodrLaneSection(lane_section)
    viewer.saveFig(output_dir + "/" + "open_drive_map_road_" + str(idx_r) + "_lane_section" + str(idx_ls) + ".png")
    viewer.show()
    viewer.clear()

for idx_r, road in open_drive_map.GetRoads().items():
  for idx_ls, lane_section in enumerate(road.lane_sections):
    for idx_l, lane in lane_section.GetLanes().items():
      viewer.drawWorld(world)
      viewer.drawXodrRoad(road, color_triplet_gray)
      viewer.drawXodrLaneSection(lane_section, color_triplet_gray)
      viewer.drawXodrLane(lane)
      viewer.saveFig(output_dir + "/" + "open_drive_map_road_" + str(idx_r) + "_lane_section" + str(idx_ls) + "_lane" + str(idx_l) + ".png")
      viewer.show()
      viewer.clear()

# XodrLanes of Roadgraph
roadgraph = map_interface.GetRoadgraph()
roadgraph.PrintGraph(output_dir + "/" + map_name)
lane_ids = roadgraph.GetAllLaneids()

for lane_id in lane_ids:
  lane_polygon = roadgraph.GetLanePolygonForLaneId(lane_id)
  # plot plan_view
  road_id = roadgraph.GetRoadForLaneId(lane_id)
  road = map_interface.GetOpenDriveMap().GetRoad(road_id)
  plan_view_reference = road.plan_view.GetReferenceLine()
  # plot polygon with center line
  viewer.drawWorld(world)
  color = list(np.random.choice(range(256), size=3)/256)
  viewer.drawPolygon2d(lane_polygon, color, 1.0)
  viewer.drawLine2d(plan_view_reference, color="red")
  viewer.saveFig(output_dir + "/" + "roadgraph_laneid_" + str(lane_id) + ".png")
  viewer.show()
  viewer.clear()

# starting on the left
comb_all = []
start_point = [Point2d(-30, -2)]
end_point_list = [Point2d(30, -2), Point2d(-2, -30)]
comb = list(itertools.product(start_point, end_point_list))
comb_all = comb_all + comb

# starting on the right
start_point = [Point2d(30, 2)]
end_point_list = [Point2d(-2, -30)]
comb = list(itertools.product(start_point, end_point_list))
comb_all = comb_all + comb

# starting on the bottom
start_point = [Point2d(2, -30)]
end_point_list = [Point2d(30, -2)]
comb = list(itertools.product(start_point, end_point_list))
comb_all = comb_all + comb

# starting on the top
start_point = [Point2d(168, 187)]
end_point_list = [Point2d(153, 172), Point2d(168, 153), Point2d(188, 168)]
comb = list(itertools.product(start_point, end_point_list))
comb_all = comb_all + comb

print("comb_all", comb_all)

cnt = 0
for start_p, end_p in comb_all:
  goal_polygon = Polygon2d([0, 0, 0],[Point2d(-1,-1),Point2d(-1,1),Point2d(1,1), Point2d(1,-1)])
  goal_polygon = goal_polygon.Translate(end_p)
  rc = map_interface.GenerateRoadCorridor(start_p, goal_polygon)
  roads = rc.roads
  road_ids = list(roads.keys())
  print(road_ids)
  
  viewer.drawWorld(world)
  viewer.drawRoadCorridor(rc, "blue")
  viewer.saveFig(output_dir + "/" + "roadcorridor_" + str(cnt) + ".png")
  viewer.show()
  viewer.clear()

  for idx, lane_corridor in enumerate(rc.lane_corridors):
    viewer.drawWorld(world)
    viewer.drawLaneCorridor(lane_corridor, "green")
    viewer.saveFig(output_dir + "/" + "roadcorridor_" + str(cnt) + "_with_driving_direction_lancecorridor" + str(idx) + ".png")
    viewer.show()
    viewer.clear()
  
  viewer.show()
  viewer.clear()
  cnt = cnt+1
