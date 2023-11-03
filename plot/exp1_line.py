import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# read data in exp1 npy
# results = []

plt.figure()
for pt1 in [0,1,5]:
    for pt2 in [90, 95, 99]:
        result = np.load(f'plot/exp1/cold_start_rate_distribution_200_{pt1}_{pt2}_0.85.npy', allow_pickle=True).item()
        # results.append(r)
        # import pdb; pdb.set_trace()
        x = np.sort(result["cold_start_rate_list"])
        sns.ecdfplot(x = x,  legend = True, label=f"pt1={pt1},pt2={pt2}")
        # hist, base = np.histogram(result["cold_start_rate_list"], density=True)
        # import pdb; pdb.set_trace()
        # cumulative = np.cumsum(hist) / np.sum(hist)
        # plt.plot(base[1:], cumulative, label=f'pt1={pt1},pt2={pt2}')
    
plt.xlabel('App Cold Start Rate(%)')
plt.ylabel('CDF')
plt.legend()
plt.savefig('plot/fig/exp1_line.pdf')
# plt.show()
