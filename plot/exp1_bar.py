import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


plt.figure()
xs = []
x_max = 0
for pt1 in [0,1,5]:
    for pt2 in [90, 95, 99]:
        result = np.load(f'plot/exp1/cold_start_rate_distribution_200_{pt1}_{pt2}_0.85.npy', allow_pickle=True).item()
        # results.append(r)
        x = result["memory_waste_time"]
        xs.append({"x":x, "pt1":pt1, "pt2":pt2})
        x_max = max(x_max, x)

for x in xs:
    x["x"] = x["x"] / x_max * 100
# sort xs
sorted_xs = sorted(xs, key=lambda k: k['x'])

x_plot = [x["x"] for x in sorted_xs]
tick_label = [f'{x["pt1"]},{x["pt2"]}' for x in sorted_xs]
sns.barplot(x = tick_label, y = x_plot,  legend = True)

# plt.xlabel('App Cold Start Rate(%)')
plt.ylabel('Normalized Memory Waste Time(%)')
plt.legend()
plt.savefig('plot/fig/exp1_bar.pdf')
# plt.show()
