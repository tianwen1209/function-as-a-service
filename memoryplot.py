from collections import defaultdict
from email.policy import default
from Application import Application
from Function import Function
import seaborn as sns
from tqdm import tqdm
from statistics import mean 
import pandas as pd
import numpy as np
from numpy import number
import pmdarima as pm
from matplotlib import pyplot as plt
import json
import time

if __name__ == "__main__":

    workload_name="day1.npy"
    function_array = np.load(workload_name)
    function_array = function_array.astype(object)
    print("size of workload: ", function_array.shape[0])
    App_memory_dict=defaultdict(list)
    App_duration_dict=defaultdict(list)
    for i in range(len(function_array)):
        App_memory_dict[function_array[i][1]].append(float(function_array[i][5]))
        App_duration_dict[function_array[i][1]].append(float(function_array[i][4]))
    #print(func_num_per_app)
    data1=[min(App_memory_dict[key]) for key in App_memory_dict.keys()]   
    data2=[mean(App_memory_dict[key]) for key in App_memory_dict.keys()]  
    data3=[max(App_memory_dict[key]) for key in App_memory_dict.keys()]  
    
    sns.ecdfplot(x = data1,  legend = True, label="Min")
    sns.ecdfplot(x = data2,  legend = True, label="Average")
    sns.ecdfplot(x = data3,  legend = True, label="Maximum")
    plt.xlabel("Allocated Memory (MB)")
    plt.ylabel("CDF")
    plt.legend()
    plt.savefig('memory.pdf')
    plt.close()

    data1=[min(App_duration_dict[key]) for key in App_duration_dict.keys()]   
    data2=[mean(App_duration_dict[key]) for key in App_duration_dict.keys()]  
    data3=[max(App_duration_dict[key]) for key in App_duration_dict.keys()]  
    
    sns.ecdfplot(x = data1,  legend = True, label="Min")
    sns.ecdfplot(x = data2,  legend = True, label="Average")
    sns.ecdfplot(x = data3,  legend = True, label="Maximum")
    plt.xlabel("Time (s)")
    plt.ylabel("CDF")
    plt.legend()
    plt.savefig('duration.pdf')


