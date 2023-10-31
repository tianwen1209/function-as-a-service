from collections import defaultdict
from Application import Application
from Function import Function

# pip install statsmodels
# pip install pmdarima
from tqdm import tqdm
from statistics import mean 
import pandas as pd
import numpy as np
from numpy import number
import pmdarima as pm
from pmdarima import model_selection
from matplotlib import pyplot as plt
import json
import time

def find_OOB_app(histogram, OOB_duration, percent_threshold):

    if len(histogram)==0:
        return []

    # output a list of app_id which has more than 25% values larger than 4 hours
    # longer than OOB_duration is regarded as outlier
    OOB_apps = []
    for id in histogram.keys():
        if len(histogram[id][1])==0:
            continue
        data = np.array(histogram[id][1])
        # check how many IT larger than max duration
        percent = np.sum(data>OOB_duration)/data.shape[0]
        if percent>percent_threshold:
            OOB_apps.append(id)

    return OOB_apps


class Simulator:
    def __init__(self):
        """_summary_

        Args:
            workload (list of Function objects): _description_
        """
        self.current_time = 0
        self.start_cold_dict = defaultdict(lambda:0)
        self.start_warm_dict = defaultdict(lambda:0)
        # {key: application id, value: [application object, list of invocations, load_time, last_finish_time, keep_live_until]}
        self.application_in_memory = {}
        self.max_memory = 0
        self.wasted_memory_time = 0
        self.update_OOB_apps = False
        self.workload = []

    def load_workload(self, app, day):
        function_array = np.load("./workload_{}/day{}.npy".format(app,day))
        function_array = function_array.astype(object)
        print("size of workload: ", function_array.shape[0])
        self.workload = []
        for i in range(len(function_array)):
            self.workload.append(Function(function_array[i][0], function_array[i][1], float(function_array[i][2]), function_array[i][3], float(function_array[i][4]), float(function_array[i][5])))

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

    def get_memory_usage(self):
        total_memory = 0
        for app_id in self.application_in_memory:
            last_finish_time = self.application_in_memory[app_id][3]
            if last_finish_time > self.current_time:
                current_memory= self.application_in_memory[app_id][1].function_memory
                total_memory += current_memory
        return total_memory

    def add_invocation(self, invocation, keep_live_time, pre_warm_time):
        # if the application is not in memory, cold start
        if not invocation.app_id in self.application_in_memory:
            self.start_cold_dict[invocation.app_id] += 1
            self.application_in_memory[invocation.app_id] = [invocation.app, invocation, invocation.start_time, invocation.end_time, pre_warm_time, keep_live_time]
            # if the application has been loaded before, check if warm start
        else:
            current_app_state = self.application_in_memory[invocation.app_id]
            # if warm start
            last_finish_time = current_app_state[3] #invocation.end_time
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

    def simulation_hybrid(self, app, app_dict, func_dict, verbose=True, total_days=6, file_start_time=0, histogram_collection_time=24*60*60, pattern_min_len=10, IT_behavior_change=0.5, pt1=5, pt2=99, window_period=0.85):
        start_time = time.time()
        self.histogram_collection_time = histogram_collection_time
        self.pattern_min_len = pattern_min_len
        self.all_histograms = []
        self.current_histogram = {}
        self.histogram_id = 0
        OOB_apps_list = []
        self.scenario_stats = [0,0,0]
        predict_next_IT = defaultdict(lambda: [None,None])
        
        cold_start_list = []
        warm_start_list = []
        for day in range(1, total_days+1):
            print("loading workload of day {}".format(day))
            self.load_workload(app, day)
            # self.workload.sort(key=lambda x:x.start_time)
            few_it_count = 0
            hist_change_count = 0
            
            self.scenario_stats = [0,0,0]
            for i, invocation in enumerate(tqdm(self.workload)):
                # if i % 100000 == 0 and i > 0:
                #     print(f"number of ARIMA / IT dist / keep alive scenario: {simulator.scenario_stats[0]} / {simulator.scenario_stats[1]} / {simulator.scenario_stats[2]}")
                #     print("few_it_count: ", few_it_count, "hist_change_count: ", hist_change_count)
                if invocation.start_time<(day-1)*24*60*60:
                    continue
                self.current_time = invocation.start_time
                # check if the app has been load in memory and record memory waste time
                self.check_alive_pre_warm(invocation.app_id)
                if verbose:
                    print('\n')
                    print('func id: ', invocation.function_id, ' | app id: ', invocation.app_id,' | func start time: ', round(self.current_time,3), ' | func duration: ', round(invocation.function_duration,3))
                    try:
                        print(f'HashApp: {[x for x in app_dict if int(app_dict[x])==int(invocation.app_id)]}')
                        print(f'HashFunction: {[x for x in func_dict if int(func_dict[x])==int(invocation.function_id)]}')
                    except Exception:
                        print("Function or App not in the dictionary")
                # create app IT histograms
                if verbose and i==0:
                    print('file start time: ', file_start_time)
                if self.current_time>=(self.histogram_id+1)*self.histogram_collection_time+file_start_time:
                    self.update_OOB_apps = True
                    self.histogram_id += 1
                    self.all_histograms.append(self.current_histogram.copy())
                    for app_id in self.current_histogram.keys():
                        # keep the previous call end time and clear idle durations
                        self.current_histogram[app_id] = [self.current_histogram[app_id][0],[],[]]
                    # if current time is still larger, append an empty historgam to all histograms
                    # print('time', self.histogram_id*self.histogram_collection_time+file_start_time, self.histogram_id)
                    while self.current_time >= (self.histogram_id+1)*self.histogram_collection_time+file_start_time:
                        self.histogram_id += 1
                        self.all_histograms.append(self.current_histogram.copy())
                        
                if invocation.app_id not in self.current_histogram.keys():
                    last_call_end_time = invocation.start_time + invocation.function_duration
                    idle_duration=[]
                    idle_end_time=[]
                    self.current_histogram[invocation.app_id] = [last_call_end_time, idle_duration, idle_end_time]
                else:
                    if invocation.start_time > self.current_histogram[invocation.app_id][0]:
                        idle_time = invocation.start_time - self.current_histogram[invocation.app_id][0]
                        self.current_histogram[invocation.app_id][2].append(invocation.start_time)
                        self.current_histogram[invocation.app_id][1].append(idle_time)
                        if verbose:
                            print('append a new idle time into current histogram: ', idle_time)
                        self.current_histogram[invocation.app_id][0] = invocation.start_time + invocation.function_duration
                    else:
                        self.current_histogram[invocation.app_id][0] = max(self.current_histogram[invocation.app_id][0], invocation.start_time+invocation.function_duration)
                    
                if verbose:
                    print('all historical histograms: [')
                    for x in self.all_histograms:
                        print('  ', x)
                    print(']')
                    print('current historgram: ')
                    print('  ', self.current_histogram)

                # check the previous histogram OOB
                if len(self.all_histograms)==0 or invocation.app_id not in self.all_histograms[-1].keys():
                    previous_histogram = []
                else:
                    previous_histogram = self.all_histograms[-1][invocation.app_id][1]
                if verbose:
                    print('func ', invocation.function_id,' previous histogram of ITs: ', previous_histogram)

                if self.update_OOB_apps:
                    OOB_apps_list = find_OOB_app(self.all_histograms[-1], OOB_duration=4*3600, percent_threshold=0.25)
                    self.update_OOB_apps = False

                pattern_represent = True
                if len(previous_histogram)<self.pattern_min_len:
                    pattern_represent = False
                    few_it_count += 1
                elif len(self.all_histograms)>1 and invocation.app_id in self.all_histograms[-2]:
                    pre_previous_histogram = self.all_histograms[-2][invocation.app_id][1]
                    if len(pre_previous_histogram)>0:
                        mean_pre = mean(previous_histogram)
                        mean_pre_pre = mean(pre_previous_histogram)
                        if abs(mean_pre-mean_pre_pre)/mean_pre_pre>=IT_behavior_change:
                            pattern_represent = False
                            # print("histogram changed")
                            hist_change_count += 1

                if verbose:
                    print('the list of OOB apps based on the previous ITs: ',OOB_apps_list, '\n')

                if len(previous_histogram)!=0:
                    previous_histogram =  np.array(previous_histogram)
                    percent5 = np.percentile(previous_histogram, pt1)
                    percent99 = np.percentile(previous_histogram, pt2)
                    histogram_range = percent99
                else:
                    # if there is no IT in previous histogram, set any value (e.g. 5 mins) for keep alive window
                    histogram_range = 300

                if len(OOB_apps_list)!=0 and invocation.app_id in OOB_apps_list and self.histogram_id>1:
                    self.scenario_stats[0]+=1
                    if verbose:
                        print('** Enter ARIMA Branch **')
                    # ! enter ARIMA with at least one complete historical histogram
                    # find all historical ITs as training data
                    training_data = []
                    for hist in self.all_histograms:
                        if invocation.app_id in hist:
                            training_data.extend(hist[invocation.app_id][1])
                    training_data = training_data + self.current_histogram[invocation.app_id][1]
                    if verbose:
                        print('training data: ', training_data)
                    if training_data != predict_next_IT[invocation.app_id][0]:
                        if len(training_data) <=3:
                            next_IT = training_data[-1]
                        else:
                            arima = pm.auto_arima(training_data, error_action='warn', trace=False,
                                                    suppress_warnings=True, maxiter=10,
                                                    seasonal=False)
                            next_IT = arima.predict(n_periods=1)[0]
                        predict_next_IT[invocation.app_id][0] = training_data
                        predict_next_IT[invocation.app_id][1] = next_IT
                    else:
                        next_IT = predict_next_IT[invocation.app_id][1]
                    prewarm_window = window_period*next_IT  # ! set pre-warm window elapse just before the next invocation
                    keep_alive_window = 2*(1-window_period)*next_IT # ! a short keep-alive window
                    predict_next_IT[invocation.app_id] = [training_data, next_IT]
                    if verbose:
                        print(f'ARIMA preficted next IT: {next_IT}')
                        print("prewarm_window: ", prewarm_window, "keep_alive_window: ", keep_alive_window)
                elif pattern_represent:
                    self.scenario_stats[1]+=1
                    if verbose:
                        print('** Enter IT Distribution Branch **')
                    # ! enter IT distribution
                    prewarm_window = percent5
                    keep_alive_window = percent99-percent5
                    if verbose:
                        print("prewarm_window: ", prewarm_window, "keep_alive_window: ", keep_alive_window)
                    # import pdb; pdb.set_trace()
                else:
                    # ! enter standard keep alive, conservative scenario
                    self.scenario_stats[2]+=1
                    if verbose:
                        print('** Enter Keep Alive Branch **')
                    prewarm_window = 0
                    keep_alive_window = histogram_range
                    if verbose:
                        print("prewarm_window: ", prewarm_window, "keep_alive_window: ", keep_alive_window)
                    # import pdb; pdb.set_trace()

                self.add_invocation(invocation=invocation, pre_warm_time=prewarm_window, keep_live_time=keep_alive_window)
                
                current_memory_usage = self.get_memory_usage()
                if current_memory_usage > self.max_memory:
                    self.max_memory = current_memory_usage

            print(f"number of ARIMA / IT dist / keep alive scenario: {self.scenario_stats[0]/len(self.workload)*100:.2f}% / {self.scenario_stats[1]/len(self.workload)*100:.2f}% / {self.scenario_stats[2]/len(self.workload)*100:.2f}%")
            
            cold_start_total = 0
            warm_start_total = 0
            for app_id in range(100):
                app_id_str = str(app_id)
                cold_start = self.start_cold_dict[app_id_str]
                warm_start = self.start_warm_dict[app_id_str]
                cold_start_total += cold_start
                warm_start_total += warm_start
            cold_start_list.append(cold_start_total)
            warm_start_list.append(warm_start_total)
            if day > 1:
                cold_start_total = cold_start_list[-1] - cold_start_list[-2]
                warm_start_total = warm_start_list[-1] - warm_start_list[-2]
            print(f"cold start: {cold_start_total}, warm start: {warm_start_total}")
            
            if day== total_days and i == len(self.workload)-1:
                self.all_histograms.append(self.current_histogram)
        
        self.simulation_time = time.time() - start_time

def main(**kwargs):
    tf = open(f"app_dict_{kwargs['app']}.json", "r")
    dict = json.load(tf)
    app_dict = dict[0]
    func_dict = dict[1]
    
    simulator = Simulator()
    simulator.simulation_hybrid(kwargs['app'], app_dict, func_dict, verbose=False,total_days=12, pt1=kwargs['pt1'], pt2=kwargs['pt2'], window_period=kwargs['window_period'])
    n = sum(simulator.scenario_stats)

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
    result = {
        "ARIMA_IT_dist_keep_alive_scenario": {
            "ARIMA": simulator.scenario_stats[0]/n*100,
            "IT_dist": simulator.scenario_stats[1]/n*100,
            "keep_alive": simulator.scenario_stats[2]/n*100
        },
        "number_of_cold_start": cold_start_total,
        "number_of_warm_start": warm_start_total,
        "cold_start_rate": cold_start_total/(cold_start_total + warm_start_total),
        "Maximum_memory_usage": simulator.max_memory,
        "memory_waste_time": simulator.wasted_memory_time,
        "Simulation_time": simulator.simulation_time,
        "cold_start_rate_list": cold_start_rate_list
    }
    # np.save(f"cold_start_rate_distribution_{kwargs['app']}_{kwargs['pt1']}_{kwargs['pt2']}_{kwargs['window_period']}.npy", cold_start_rate_list)
    np.save(f"cold_start_rate_distribution_{kwargs['app']}_{kwargs['pt1']}_{kwargs['pt2']}_{kwargs['window_period']}.npy", result)


    print("\n")
    print("----------------------------------------------------")
    print(f"number of ARIMA / IT dist / keep alive scenario: {simulator.scenario_stats[0]/n*100:.2f}% / {simulator.scenario_stats[1]/n*100:.2f}% / {simulator.scenario_stats[2]/n*100:.2f}%")
    print("number of cold start: {}".format(cold_start_total))
    print("number of warm start: {}".format(warm_start_total))
    print("cold start rate: {}".format(cold_start_total/(cold_start_total + warm_start_total)))
    print("Maximum memory usage: {}".format(simulator.max_memory))
    print("memory waste time: {}".format(simulator.wasted_memory_time))
    print("Simulation time: {}".format(simulator.simulation_time))
    print("----------------------------------------------------")
    

if __name__ == "__main__":

    # function_id, app_id, start_time, trigger, function_duration, function_memory
    # function_list = [
    #     Function(0, 0, 0, 'HTTP', 3, 1), 
    #     Function(0, 0, 2, 'HTTP', 5, 1), 
    #     Function(0, 0, 7.5, 'HTTP', 4, 1), 
    #     Function(0, 0, 13, 'HTTP', 4, 1), 
    #     Function(2, 1, 5, 'HTTP', 4, 1),
    #     Function(3, 1, 11, 'HTTP', 1, 1),
    #     Function(4, 1, 15, 'HTTP', 4, 1),
    #     Function(5, 1, 20, 'HTTP', 1, 1)
    # ]
    # for pt1 in [0,1,5]:
    #     for pt2 in [99,95,90]:
    for window_period in [0.5,0.65,0.75,0.85,0.9]:
        main(app=5,pt1=5,pt2=95,window_period=window_period)