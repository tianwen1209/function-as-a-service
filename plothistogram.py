from pickle import TRUE
from Application import Application
from Function import Function

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

app_num = 200
tf = open(f"app_dict_{app_num}.json", "r")
dict = json.load(tf)
app_dict = dict[0]
func_dict = dict[1]

app_id_plot = [1,2,3,4,12,30,55,66,90,97]


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
        self.start_cold = 0
        self.start_warm = 0
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

    def plot_hybrid(self, verbose=True, total_days=6,file_start_time=0, histogram_collection_time=24*60*60, pattern_min_len=10, IT_behavior_change=0.5):
        start_time = time.time()
        self.histogram_collection_time = histogram_collection_time
        self.pattern_min_len = pattern_min_len
        self.all_histograms = []
        self.current_histogram = {}
        self.histogram_id = 0
        OOB_apps_list = []
        self.scenario_stats = [0,0,0]
        
        app_id_list = []
        for day in range(1, total_days+1):
            print("loading workload of day {}".format(day))
            self.load_workload(app_num, day)
            # self.workload.sort(key=lambda x:x.start_time)

            for i, invocation in enumerate(tqdm(self.workload)):
                # if int(invocation.app_id) not in app_id_plot:
                #     continue
                if invocation.start_time< (day-1)*24*60*60:
                    continue
                # ! all app plot
                if int(invocation.app_id) not in app_id_list:
                    app_id_list.append(int(invocation.app_id))
                self.current_time = invocation.start_time

                if self.current_time>=(self.histogram_id+1)*self.histogram_collection_time+file_start_time:
                    # print(self.current_time, (self.histogram_id+1)*self.histogram_collection_time+file_start_time)
                    self.update_OOB_apps = True
                    self.histogram_id += 1

                    # print('Y ', len(self.all_histograms))
                    self.all_histograms.append(self.current_histogram.copy())
                    # print('X ', len(self.all_histograms))

                    for app_id in self.current_histogram.keys():
                        # keep the previous call end time and clear idle durations
                        self.current_histogram[app_id] = [self.current_histogram[app_id][0],[],[]]
                    # if current time is still larger, append an empty historgam to all histograms
                    # print('time', self.histogram_id*self.histogram_collection_time+file_start_time, self.histogram_id)
                    while self.current_time >= (self.histogram_id+1)*self.histogram_collection_time+file_start_time:
                        self.histogram_id += 1
                        self.all_histograms.append(self.current_histogram.copy())
                    # print('L ', len(self.all_histograms))

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

            if day== total_days and i == len(self.workload)-1:
                self.all_histograms.append(self.current_histogram)
                
        return app_id_list
    
    
if __name__ == "__main__":

    import matplotlib.colors as mcolors
    c = mcolors.TABLEAU_COLORS
    c = [ x for x in c]

    simulator = Simulator()
    app_id_list = simulator.plot_hybrid(verbose=False, total_days=3)
    
    print('app_id_list', len(app_id_list))
    # split hist into n/10 pics
    app_in_one_plot = 10
    for j in range(int(len(app_id_list)/app_in_one_plot)):
        print(j)
        plt.figure() 
        app_id_list_slice = app_id_list[j*app_in_one_plot:(j+1)*app_in_one_plot]
        n_his = len(simulator.all_histograms)
        fig, axs = plt.subplots(nrows=len(app_id_list_slice), ncols=n_his,figsize=(len(app_id_list_slice)*2,n_his*3))
        for i,app in enumerate(app_id_list_slice):
            for day in range(n_his):
                # print(i, app, day)
                # print(simulator.all_histograms[day][str(app)][1])
                axs[i,day].hist(simulator.all_histograms[day][str(app)][1],bins=10,color=c[i%len(c)])
                if i==len(app_id_list_slice)-1:
                    axs[i,day].set_xlabel(f'day_{day+1}')
                if day==0:
                    axs[i,day].set_ylabel(f'app_{app}')
        plt.savefig(f'saved_figures/hist{j}.pdf')
        plt.close()