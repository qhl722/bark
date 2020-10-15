// Copyright (c) 2020 fortiss GmbH
//
// Authors: Julian Bernhard, Klemens Esterle, Patrick Hart and
// Tobias Kessler
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include <tuple>

#include "bark/models/behavior/constant_acceleration/constant_acceleration.hpp"
#include "bark/world/observed_world.hpp"

namespace bark {
namespace models {
namespace behavior {

Trajectory RSSBehavior::Plan(
    float min_planning_time, const world::ObservedWorld& observed_world) {
  SetBehaviorStatus(BehaviorStatus::VALID);

  const auto& lane_corr = observed_world.GetLaneCorridor();
  if (!lane_corr) {
    LOG(INFO) << "Agent " << observed_world.GetEgoAgentId()
              << ": Behavior status has expired!" << std::endl;
    SetBehaviorStatus(BehaviorStatus::EXPIRED);
    return GetLastTrajectory();
  }

  if (rss_behavior_status_ == RSSBehaviorStatus::NORMAL_BEHAVIOR) {
    // execute normal
    sub_behavior_model_->Plan(min_planning_time, observed_world);
  } else {
    safety_behavior_model_->Plan(min_planning_time, observed_world);
  }

  // TODO: set action and traj

  // set values
  Trajectory traj = std::get<0>(traj_action);
  Action action = std::get<1>(traj_action);
  SetLastTrajectory(traj);
  SetLastAction(action);
  return traj;
}


}  // namespace behavior
}  // namespace models
}  // namespace bark
