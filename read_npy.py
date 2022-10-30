from pip import main
from Application import Application
from Function import Function
import pandas as pd
import numpy as np
from numpy import number
from collections import defaultdict
import time


data = np.load('day1.npy')
# print(data)
for i,x in enumerate(data):
    print(f'{1} func_{x[0]} app_{x[1]} start time_{x[2]} {x[3]} duration_{round(float(x[4]),2)}')
    if i>10:
        break

