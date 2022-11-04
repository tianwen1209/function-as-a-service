import numpy as np
from tqdm import tqdm
from collections import defaultdict

from Function import Function


class Simulator:
    def __init__(self):
        """_summary_

        Args:
            workload (list of Function objects): _description_
        """
        self.seconds_one_day = 24*60*60
        self.current_time = 0
        self.start_cold_dict = defaultdict(lambda:0)
        self.start_warm_dict = defaultdict(lambda:0)
        # {key: application id, value: [application object, list of invocations, load_time, last_finish_time, pre_warm_time, keep_alive_time]}
        self.application_in_memory = {}
        self.max_memory = 0

        # if isinstance(workload, str):
        #     self.workload = []
        #     function_array = np.load(workload)
        #     function_array = function_array.astype(object) 
        #     print("size of workload: ", function_array.shape[0]) #size of workload:  3691
        #     '''
        #     def __init__(self, function_id, app_id, start_time, trigger, function_duration, function_memory)
        #     print(function_array[0][0]) function_id
        #     print(function_array[0][1]) app_id
        #     print(function_array[0][2]) start_time
        #     print(function_array[0][3]) trigger
        #     print(function_array[0][4]) function_duration
        #     print(function_array[0][5]) function_memory                   
        #     21
        #     2
        #     10091.231581854454
        #     http
        #     7.047086412106442
        #     144.303358036344
        #     '''
        #     for i in range(len(function_array)):
        #         self.workload.append(Function(function_array[i][0], function_array[i][1], float(function_array[i][2]), function_array[i][3], float(function_array[i][4]), float(function_array[i][5])))            
        # else:
        #     self.workload = workload
        self.workload = []
        self.wasted_memory_time = 0

    def load_workload(self, day):
        function_array = np.load("./workload_100/day{}.npy".format(day))
        function_array = function_array.astype(object)
        print("size of workload: ", function_array.shape[0])
        self.workload = []
        for i in range(len(function_array)):
            self.workload.append(Function(function_array[i][0], function_array[i][1], float(function_array[i][2]), function_array[i][3], float(function_array[i][4]), float(function_array[i][5])))

    def simulation_fixed_keep_alive(self, keep_live_time):
        self.workload.sort(key=lambda x:x.start_time)
        for i, invocation in enumerate(tqdm(self.workload)):
            self.current_time = invocation.start_time
            self.check_alive(keep_live_time)

            # if the application is not in memory, cold start
            if not invocation.app_id in self.application_in_memory:
                self.start_cold_dict[invocation.app_id] += 1
                self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, invocation.end_time + keep_live_time]
             # if the application is already in memory, warm start
            else:
                self.start_warm_dict[invocation.app_id] += 1
                current_app_state = self.application_in_memory[invocation.app_id]
                # update memory waste time
                if current_app_state[3] < invocation.start_time:
                    self.wasted_memory_time += invocation.start_time - current_app_state[3]
                current_app_state[1] = invocation
                # if the new invocation of the application ends later than all existing invocations, updated the end_time and keep_alive_until time
                if invocation.end_time > current_app_state[3]:
                    current_app_state[3] = invocation.end_time
                    current_app_state[4] = invocation.end_time + keep_live_time
                # if the new invocation uses more memory, update memory usage
                if invocation.app.app_memory > current_app_state[0].app_memory:
                    current_app_state[0] = invocation.app
            
            current_memory_usage = self.get_memory_usage()
            if current_memory_usage > self.max_memory:
                self.max_memory = current_memory_usage

    def add_invocation(self, invocation, keep_live_time, pre_warm_time):
        # if the application is not in memory, cold start
        if not invocation.app_id in self.application_in_memory:
            self.start_cold_dict[invocation.app_id] += 1
            self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, pre_warm_time, keep_live_time]
            # if the application has been loaded before, check if warm start
        else:
            current_app_state = self.application_in_memory[invocation.app_id]
            # if warm start
            last_finish_time = current_app_state[3]
            if last_finish_time > invocation.start_time:
                self.start_warm_dict[invocation.app_id] += 1
                # updated the end_time and keep_alive_until time
                if invocation.end_time > last_finish_time:
                    current_app_state[1] = invocation
                    current_app_state[3] = invocation.end_time
                    current_app_state[4] = pre_warm_time
                    current_app_state[5] = keep_live_time
            else:
                previous_pre_warm_time = current_app_state[4]
                pre_warm_load_time = last_finish_time + previous_pre_warm_time
                if pre_warm_load_time <= self.current_time:
                    self.start_warm_dict[invocation.app_id] += 1
                    # update memory waste time (only happens for the case of pre-warm)
                    self.wasted_memory_time += invocation.start_time - pre_warm_load_time
                    current_app_state[1] = invocation
                    current_app_state[3] = invocation.end_time
                    current_app_state[4] = pre_warm_time
                    current_app_state[5] = keep_live_time
                else:
                    self.start_cold_dict[invocation.app_id] += 1
                    self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, pre_warm_time, keep_live_time]

    def simulation_pre_warm(self, keep_live_time, pre_warm_time, total_days):
        for day in range(1, total_days+1):
            print("loading workload of day {}".format(day))
            self.load_workload(day)
            for i, invocation in enumerate(tqdm(self.workload)):
                self.current_time = invocation.start_time
                self.check_alive_pre_warm(invocation.app_id)
                # print(self.application_in_memory)
                self.add_invocation(invocation=invocation, pre_warm_time=pre_warm_time, keep_live_time=keep_live_time)
                
                current_memory_usage = self.get_memory_usage()
                if current_memory_usage > self.max_memory:
                    self.max_memory = current_memory_usage

    def get_memory_usage(self):
        total_memory = 0
        for app_id in self.application_in_memory:
            last_finish_time = self.application_in_memory[app_id][3]
            if last_finish_time > self.current_time:
                current_memory= self.application_in_memory[app_id][1].function_memory
                total_memory += current_memory
        return total_memory

    def check_alive(self, keep_live_time):
        for app_id in self.application_in_memory:
            current_app_alive_until = self.application_in_memory[app_id][4]
            if current_app_alive_until <= self.current_time:
                # update memory waste time
                self.wasted_memory_time += keep_live_time
                del self.application_in_memory[app_id]
    
    def check_alive_pre_warm(self, app_id):
        if app_id in self.application_in_memory:
        # {key: application id, value: [application object, list of invocations, load_time, last_finish_time, pre_warm_time, keep_live_time]}
            pre_warm_time = self.application_in_memory[app_id][4]
            keep_live_time = self.application_in_memory[app_id][5]
            last_finish_time = self.application_in_memory[app_id][3]
            # if prewarm+keep live finishes before current time, record wast time.
            if last_finish_time < self.current_time:
                # print(current_app_alive_until)
                # print(pre_warm_time)
                pre_warm_load_time = last_finish_time + pre_warm_time
                if pre_warm_load_time <= self.current_time:
                    if pre_warm_load_time + keep_live_time < self.current_time:
                        del self.application_in_memory[app_id]
                        # update memory waste time
                        self.wasted_memory_time += keep_live_time
        else:
            return


if __name__ == "__main__":
    # function1 = Function(0, 0, 0, 'http', 3, 1)
    # function2 = Function(1, 0, 5, 'http', 3, 1)
    # function3 = Function(2, 1, 3, 'http', 5, 1)
    # function4 = Function(0, 0, 7.5, 'http', 1, 1)
    # function_list = [function1, function2, function3, function4]
    # function_list = [
    #     Function(0, 0, 0, 3), 
    #     Function(0, 0, 2, 5), 
    #     Function(0, 0, 7.5, 4), 
    #     Function(0, 0, 13, 4), 
    #     # Function(0, 0, 15, 2), 
    #     # Function(0, 0, 13, 1), 
    #     # Function(0, 0, 18, 2), 
    #     # Function(1, 0, 7, 4),
    #     Function(2, 1, 5, 4),
    #     Function(3, 1, 11, 1),
    #     Function(4, 1, 15, 4),
    #     Function(5, 1, 20, 1)
    # ]
    # simulator = Simulator(function_list)
    simulator = Simulator()
    # simulator.simulation_fixed_keep_alive(10)
    simulator.simulation_pre_warm(600, 0, 12)

    cold_start_total = 0
    warm_start_total = 0
    cold_start_rate_list = []
    # print(simulator.start_cold_dict)
    # print(len(simulator.start_cold_dict))
    # print(len(simulator.start_warm_dict))
    for app_id in range(100):
        app_id_str = str(app_id)
        cold_start = simulator.start_cold_dict[app_id_str]
        warm_start = simulator.start_warm_dict[app_id_str]
        cold_start_total += cold_start
        warm_start_total += warm_start
        if cold_start + warm_start > 0:
            cold_start_rate_list.append(cold_start/(cold_start+warm_start))
    
    cold_start_rate_list = np.array(cold_start_rate_list)
    np.save("cold_start_rate_distribution_fix_600.npy", cold_start_rate_list)

    print("number of cold start: {}".format(cold_start_total))
    print("number of warm start: {}".format(warm_start_total))
    print("cold start rate: {}".format(cold_start_total/(cold_start_total + warm_start_total)))
    print("Maximum memory usage: {}".format(simulator.max_memory))
    print("memory waste time: {}".format(simulator.wasted_memory_time))

    # x = simulator.get_all_app_full_IT_trace()
    # print(x)
    # simulator.simulation_auto_arima(x)