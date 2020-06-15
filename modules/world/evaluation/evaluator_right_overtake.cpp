// Copyright (c) 2020 fortiss GmbH
//
// This work is licensed under the terms of the MIT license.
// For a copy, see <https://opensource.org/licenses/MIT>.

#include "modules/world/evaluation/evaluator_right_overtake.hpp"

#include "modules/world/evaluation/labels/behind_of_label_function.hpp"
#include "modules/world/evaluation/labels/dense_traffic_label_function.hpp"
#include "modules/world/evaluation/labels/front_of_label_function.hpp"
#include "modules/world/evaluation/labels/right_of_label_function.hpp"

namespace modules {
namespace world {
namespace evaluation {
const char EvaluatorRightOvertake::formula_[] =
    "G (dense -> !(b_v#0 & X[!](b_v#0 U r_v#0 U f_v#0)))";

const LabelFunctions EvaluatorRightOvertake::labels_ = {
    LabelFunctionPtr(new DenseTrafficLabelFunction("dense", 20.0, 8)),
    LabelFunctionPtr(new RightOfLabelFunction("r_v")),
    LabelFunctionPtr(new FrontOfLabelFunction("f_v")),
    LabelFunctionPtr(new BehindOfLabelFunction("b_v"))};

const char EvaluatorDense::formula_[] =
    "G !dense";

const LabelFunctions EvaluatorDense::labels_ = {
    LabelFunctionPtr(new DenseTrafficLabelFunction("dense", 20.0, 8))};

}  // namespace evaluation
}  // namespace world
}  // namespace modules
