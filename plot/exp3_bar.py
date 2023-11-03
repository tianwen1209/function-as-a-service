import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


plt.figure()
xs = []
x_max=0
for cv in [0,2,5,10]:
    result = np.load(f'plot/exp3/cold_start_rate_distribution_200_5_95_{cv}.npy', allow_pickle=True).item()
    # results.append(r)
    x = result["memory_waste_time"]
    xs.append({"x":x, "cv":cv})
    x_max = max(x_max, x)

for x in xs:
    x["x"] = x["x"] / x_max * 100
# sort xs
sorted_xs = sorted(xs, key=lambda k: k['x'])

x_plot = [x["x"] for x in sorted_xs]
tick_label = [f'{x["cv"]}' for x in sorted_xs]
sns.barplot(x = tick_label, y = x_plot,  legend = True)

# plt.xlabel('App Cold Start Rate(%)')
plt.ylabel('Normalized Memory Waste Time(%)')
plt.legend()
plt.savefig('plot/fig/exp3_bar.pdf')
# plt.show()
