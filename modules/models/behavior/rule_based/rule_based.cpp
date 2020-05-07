// Copyright (c) 2019 fortiss GmbH, Julian Bernhard, Klemens Esterle, Patrick
// Hart, Tobias Kessler
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include "modules/models/behavior/rule_based/rule_based.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <memory>
#include <utility>
#include <tuple>

#include "modules/commons/transformation/frenet.hpp"
#include "modules/world/observed_world.hpp"
#include "modules/models/dynamic/single_track.hpp"
#include "modules/models/dynamic/integration.hpp"

namespace modules {
namespace models {
namespace behavior {

using modules::commons::transformation::FrenetPosition;
using modules::geometry::Point2d;
using modules::models::dynamic::State;
using modules::models::dynamic::StateDefinition;
using modules::world::objects::Agent;
using modules::world::objects::AgentPtr;
using modules::models::dynamic::DynamicModelPtr;

//! IDM Model will assume other front vehicle as constant velocity during
Trajectory BehaviorRuledBased::Plan(
    float delta_time, const world::ObservedWorld& observed_world) {
  using dynamic::StateDefinition;
  SetBehaviorStatus(BehaviorStatus::VALID);

  // whether to change lanes or not
  // TODO(@hart): while changing lanes do not decide again
  std::pair<LaneChangeDecision, LaneCorridorPtr> lane_res =
    CheckIfLaneChangeBeneficial(const ObservedWorld& observed_world);
  SetLaneCorridor(lane_res.second);

  if (!GetLaneCorridor()) {
    return GetLastTrajectory();
  }

  std::tuple<double, double, bool> rel_values = CalcRelativeValues(
    observed_world,
    GetLaneCorridor());

  // if the vehicle is on a different LaneCorr. than the set LaneCorr.
  // this only is in effect when setting a different LaneCorr
  if (GetLaneCorridor() != observed_world.GetLaneCorridor()) {
    std::tuple<double, double, bool> rel_values_ego_corr = CalcRelativeValues(
      observed_world,
      observed_world.GetLaneCorridor());
    // vehicle on ego LaneCorr. is closer
    if (std::get<0>(rel_values_ego_corr) < std::get<0>(rel_values)) {
      rel_values = rel_values_ego_corr;
    }
  }

  std::tuple<Trajectory, Action> traj_action =
    GenerateTrajectory(
      observed_world, GetLaneCorridor(), rel_values, delta_time);

  // set values
  Trajectory traj = std::get<0>(traj_action);
  Action action = std::get<1>(traj_action);
  SetLastTrajectory(traj);
  SetLastAction(action);
  return traj;
}

}  // namespace behavior
}  // namespace models
}  // namespace modules
