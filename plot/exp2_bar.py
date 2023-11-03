import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


plt.figure()
xs = []
x_max=0
for window in [0.5,0.65,0.75,0.85,0.9]:
    result = np.load(f'plot/exp2/cold_start_rate_distribution_200_5_95_{window}.npy', allow_pickle=True).item()
    # results.append(r)
    x = result["memory_waste_time"]
    xs.append({"x":x, "window":window})
    x_max = max(x_max, x)

for x in xs:
    x["x"] = x["x"] / x_max * 100
# sort xs
sorted_xs = sorted(xs, key=lambda k: k['x'])

x_plot = [x["x"] for x in sorted_xs]
tick_label = [f'{x["window"]}' for x in sorted_xs]
sns.barplot(x = tick_label, y = x_plot,  legend = True)

plt.xlabel('Window Size Ratio')
plt.ylabel('Normalized Memory Waste Time(%)')
plt.legend()
plt.savefig('plot/fig/exp2_bar.pdf')
# plt.show()
