import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# read data in exp1 npy
# results = []

plt.figure()
for cv in [0,2,5,10]:
    result = np.load(f'plot/exp3/cold_start_rate_distribution_200_5_95_{cv}.npy', allow_pickle=True).item()
    # results.append(r)
    # import pdb; pdb.set_trace()
    x = np.sort(result["cold_start_rate_list"])
    sns.ecdfplot(x = x,  legend = True, label=f"c={cv}")
    # hist, base = np.histogram(result["cold_start_rate_list"], density=True)
    # import pdb; pdb.set_trace()
    # cumulative = np.cumsum(hist) / np.sum(hist)
    # plt.plot(base[1:], cumulative, label=f'pt1={pt1},pt2={pt2}')
    
plt.xlabel('App Cold Start Rate(%)')
plt.ylabel('CDF')
plt.legend()
plt.savefig('plot/fig/exp3_line.pdf')
# plt.show()
