import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# read data in exp1 npy
# results = []

plt.figure()
for window in [0.5,0.65,0.75,0.85,0.9]:
    result = np.load(f'plot/exp2/cold_start_rate_distribution_200_5_95_{window}.npy', allow_pickle=True).item()
    # results.append(r)
    # import pdb; pdb.set_trace()
    x = np.sort(result["cold_start_rate_list"])
    sns.ecdfplot(x = x,  legend = True, label=f"window={window}")
    
plt.xlabel('App Cold Start Rate(%)')
plt.ylabel('CDF')
plt.legend()
plt.savefig('plot/fig/exp2_line.pdf')
# plt.show()
