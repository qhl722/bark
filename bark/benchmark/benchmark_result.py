# Copyright (c) 2019 fortiss GmbH
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import os
import pickle
import pandas as pd
import logging
import re
import zipfile
import math

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


class BehaviorConfig:
    def __init__(self, behavior_name, behavior, param_descriptions=None):
        self.behavior_name = behavior_name
        self.behavior = behavior
        self.param_descriptions = param_descriptions or {}

    def as_dict(self):
        dct = {"behavior": self.behavior_name, **self.param_descriptions}
        return dct

    @staticmethod
    def configs_from_dict(behavior_dict):
        behavior_configs = []
        for behavior_name, behavior in behavior_dict.items():
            config = BehaviorConfig(behavior_name, behavior)
            behavior_configs.append(config)
        return behavior_configs

# contains information for a single benchmark run
class BenchmarkConfig:
    def __init__(self, config_idx, behavior_config,
                 scenario, scenario_idx, scenario_set_name):
        self.config_idx = config_idx
        self.behavior_config = behavior_config
        self.scenario = scenario
        self.scenario_idx = scenario_idx
        self.scenario_set_name = scenario_set_name

    def get_info_string_list(self):
        info_strings = ["ConfigIdx: {}".format(self.config_idx),
                        "Behavior: {}".format(self.behavior_config.behavior_name),
                        "ScenarioSet: {}".format(self.scenario_set_name),
                        "ScenarioIdx: {}".format(self.scenario_idx)]
        return info_strings

    def as_dict(self):
        return {"config_idx": self.config_idx,
                "scen_set": self.scenario_set_name,
                "scen_idx": self.scenario_idx,
                **self.behavior_config.as_dict()}

    def get_evaluation_groups(self):
      return ["scen_set", *list(self.behavior_config.as_dict().keys())]


# result of benchmark run
class BenchmarkResult:
    def __init__(self, result_dict = None, benchmark_configs = None, histories = None, data_frame = None, file_name = None):
        self.__result_dict = result_dict or []
        self.__benchmark_configs = benchmark_configs or []
        if isinstance(data_frame, pd.DataFrame):
            self.__data_frame = data_frame
        else:
            self.__data_frame = None
        self.__histories = histories or {}
        self.__file_name = file_name or None

    def get_data_frame(self):
        if not isinstance(self.__data_frame, pd.DataFrame):
            self.__data_frame = pd.DataFrame(self.__result_dict)
        return self.__data_frame

    def get_result_dict(self):
        if len(self.__result_dict) == 0 and isinstance(self.__data_frame, pd.DataFrame):
            self.__result_dict = self.__data_frame.to_dict("records")
        return self.__result_dict

    def get_benchmark_configs(self):
        return self.__benchmark_configs

    def get_histories(self):
        return self.__histories

    def get_benchmark_config(self, config_idx):
        return BenchmarkResult.find_benchmark_config(
            self.__benchmark_configs, config_idx)

    def get_benchmark_config_indices(self):
        return [bc.config_idx for bc in self.__benchmark_configs]

    def get_history(self, config_idx):
        return self.__histories[config_idx]

    def get_evaluation_groups(self):
        evaluation_groups = {"scen_set"}
        for conf in self.__benchmark_configs:
            evaluation_groups.update(set(conf.get_evaluation_groups()))
        return list(evaluation_groups)

    def get_file_name(self):
        return self.__file_name

    @staticmethod
    def find_benchmark_config(benchmark_configs, config_idx):
        for config in benchmark_configs:
            if config.config_idx == config_idx:
                return config
        return None

    @staticmethod
    def _sort_bench_confs(benchmark_configs):
        def sort_key(bench_conf):
            return bench_conf.config_idx
        benchmark_configs.sort(key=sort_key)

    @staticmethod
    def load_pickle(filename):
        with open(filename, 'rb') as handle:
            dmp = pickle.load(handle)
        return dmp

    @staticmethod
    def load(filename, load_configs=False, load_histories=False):
        if filename.endswith(".pickle"):
            return BenchmarkResult.load_pickle(filename)
        else:
            rst = BenchmarkResult.load_results(filename)
            if load_configs:
                rst.load_benchmark_configs()
            if load_histories:
                rst.load_histories()
            return rst

    def load_histories(self, config_idx_list = None):
        if config_idx_list:
            existing_history_config_indices = self.__histories.keys()
            configs_idx_to_load = list(set(config_idx_list) - set(existing_history_config_indices))
        else:
            configs_idx_to_load = None # all available histories are loaded
        new_histories = None
        with zipfile.ZipFile(self.__file_name, 'r') as result_zip_file:
            new_histories, configs_not_found, processed_files = BenchmarkResult._load_and_merge(result_zip_file, \
                "histories", configs_idx_to_load)
        if len(configs_not_found) > 0:
            logging.warning("The histories with config indices {} were not found in {}".format(configs_not_found, self.__file_name))
        if new_histories:
            new_result = BenchmarkResult(result_dict=None, benchmark_configs=None,
                              histories=new_histories)
            self.extend(new_result)
        return processed_files

    def load_benchmark_configs(self, config_idx_list = None):
        if config_idx_list:
            existing_config_indices = self.get_benchmark_config_indices()
            configs_idx_to_load = list(set(config_idx_list) - set(existing_config_indices))
        else:
            configs_idx_to_load = None # all available configs are loaded
        new_bench_configs = None
        with zipfile.ZipFile(self.__file_name, 'r') as result_zip_file:
            new_bench_configs, configs_not_found, processed_files = BenchmarkResult._load_and_merge(result_zip_file, \
                "configs", configs_idx_to_load)
        if len(configs_not_found) > 0:
            logging.warning("The benchmark configs with indices {} were not found in {}".format(configs_not_found, self.__file_name))
        if new_bench_configs:
            new_result = BenchmarkResult(result_dict=None, benchmark_configs=new_bench_configs,
                              histories=None)
            self.extend(new_result)
        return processed_files

    @staticmethod
    def _find_files_to_load(total_file_list, filetype, config_idx_list):
        files_to_load = []
        configs_not_found = set(config_idx_list)
        for file in total_file_list:
            match = re.search("config_idx_(?P<from>[0-9]+)_to_(?P<to>[0-9]+).{}".format(filetype), file)
            if not match:
                continue
            range_dct = match.groupdict()
            found_config = list(filter(lambda conf_idx: conf_idx >= int(range_dct["from"]) \
                                 and conf_idx <= int(range_dct["to"]), config_idx_list))
            configs_not_found -= set(found_config)
            if len(found_config) > 0:
                files_to_load.append(file)
        return files_to_load, configs_not_found

    @staticmethod
    def _load_and_merge(zip_file_handle, filetype, config_idx_list):
        total_file_list = [filename for filename in zip_file_handle.namelist() \
                        if filetype in filename]
        configs_not_found = []
        if len(total_file_list) < 1:  
            logging.warning("There are no files for type: {}. Have you forgotten to specify it in dump()?".format(filetype))
        files_to_load = total_file_list
        if config_idx_list:
            files_to_load, configs_not_found = BenchmarkResult._find_files_to_load(total_file_list, \
                filetype, config_idx_list)
        merged_iterable = None
        for file in files_to_load:
            bytes = zip_file_handle.read(file)
            iterable = pickle.loads(bytes)
            if isinstance(iterable, list):
                if not merged_iterable:
                    merged_iterable = []
                merged_iterable.extend(iterable)
            elif isinstance(iterable, dict):
                if not merged_iterable:
                    merged_iterable = {}
                merged_iterable.update(iterable)
        return merged_iterable, configs_not_found, files_to_load

    @staticmethod
    def _save_and_split(zip_file_handle, filetype, pickable_iterable, max_bytes_per_file):
        whole_list_byte_size = len(pickle.dumps(pickable_iterable, \
                                      protocol=pickle.HIGHEST_PROTOCOL))
        num_files = math.ceil(whole_list_byte_size/max_bytes_per_file)
        num_configs_per_file = math.floor(len(pickable_iterable)/num_files)
        config_idx_list = list(range(0, len(pickable_iterable)))
        config_idx_splits = [config_idx_list[i:i + num_configs_per_file] \
                     for i in range(0, len(config_idx_list), num_configs_per_file)]
        for config_idx_split in config_idx_splits:
            iterable_to_write = None
            if isinstance(pickable_iterable, list):
                iterable_to_write = [pickable_iterable[i] for i in config_idx_split]
            elif isinstance(pickable_iterable, dict):
                iterable_to_write = { config_idx : pickable_iterable[config_idx] \
                                      for config_idx in config_idx_split}

            filename = os.path.join(filetype, "config_idx_{}_to_{}.{}".format(
                  config_idx_split[0], config_idx_split[-1], filetype))
            zip_file_handle.writestr( filename, pickle.dumps(iterable_to_write, \
                                                protocol=pickle.HIGHEST_PROTOCOL))

    def _dump_results(self, zip_file_handle):
        zip_file_handle.writestr("benchmark.results", \
            pickle.dumps(self.get_data_frame(), protocol=pickle.HIGHEST_PROTOCOL))

    def _dump_histories(self, zip_file_handle, max_bytes_per_file):
        if not self.get_histories():
            return
        BenchmarkResult._save_and_split(zip_file_handle, "histories", \
          self.get_histories(), max_bytes_per_file  )

    def _dump_benchmark_configs(self, zip_file_handle, max_bytes_per_file):
        if not self.get_benchmark_configs():
            return
        BenchmarkResult._save_and_split(zip_file_handle, "configs", \
          self.get_benchmark_configs(), max_bytes_per_file  )

    @staticmethod
    def load_results(filename):
        with zipfile.ZipFile(filename, 'r') as result_zip_file:
            bytes = result_zip_file.read("benchmark.results")
        data_frame = pickle.loads(bytes)
        return BenchmarkResult(data_frame = data_frame, file_name = filename)

    def dump(self, filename, dump_configs=False, dump_histories=False, max_mb_per_file=1000):
        with zipfile.ZipFile(filename, 'w') as result_zip_file:
            self._dump_results(result_zip_file)
            if dump_configs:
                self._dump_benchmark_configs(result_zip_file, max_mb_per_file*10**6)
            if dump_histories:
                self._dump_histories(result_zip_file, max_mb_per_file*10**6)
        logging.info("Saved BenchmarkResult to {}".format(
            os.path.abspath(filename)))

    def extend(self, benchmark_result):
        new_idxs = benchmark_result.get_benchmark_config_indices()
        this_idxs = self.get_benchmark_config_indices()
        overlap = set(new_idxs) & set(this_idxs)
        if len(overlap) != 0:
            raise ValueError("Overlapping config indices. No extension possible.")
        self.__result_dict.extend(benchmark_result.get_result_dict())
        self.__benchmark_configs.extend(benchmark_result.get_benchmark_configs())

        other_data_frame = benchmark_result.get_data_frame()
        if isinstance(self.__data_frame, pd.DataFrame):
            if isinstance(other_data_frame, pd.DataFrame):
                self.__data_frame = pd.concat((self.__data_frame, other_data_frame))
        else:
            if isinstance(other_data_frame, pd.DataFrame):
                self.__data_frame = other_data_frame
        self.__histories.update(benchmark_result.get_histories())