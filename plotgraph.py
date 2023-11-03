import json
from re import X
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import seaborn as sns
import pandas as pd
from pandas import Series,DataFrame

mpl.use('Agg')

if __name__ == "__main__":
    data_root='./'
    tf = open("app_dict_3.json", "r")
    tmp = json.load(tf)
    app_dict = tmp[0]
    function_dict = tmp[1]  
    func_num_per_app=[set() for i in range(len(app_dict.keys()))]  
    invocation_list=[]
    function_list=[-1 for i in range(len(function_dict.keys()))]
    for i in range(1,13):
        invocations_function=pd.read_csv("{}invocations_per_function_md.anon.d{:02d}.csv".format(data_root, i))   
        for index, row in invocations_function.iterrows():
            function_id = row['HashFunction']
            app_id = row['HashApp']
            if not function_id in function_dict or not app_id in app_dict:
                continue
            else:
                func_num_per_app[app_dict[app_id]].add(function_dict[function_id])
                invocation_list.append(app_dict[app_id])
                function_list[function_dict[function_id]]=app_dict[app_id]
    #print(func_num_per_app)
    data1=[len(term) for term in func_num_per_app]   
    data2=[data1[id] for id in invocation_list]
    data3=[data1[id] for id in function_list]
    
    sns.ecdfplot(x = data1,  legend = True, label="% of Apps")
    sns.ecdfplot(x = data2,  legend = True, label="% of Invocations")
    sns.ecdfplot(x = data3,  legend = True, label="% of Functions")
    plt.xlabel("Functions per App")
    plt.ylabel("Cumulative Fraction")
    plt.legend()
    plt.savefig('test.pdf')