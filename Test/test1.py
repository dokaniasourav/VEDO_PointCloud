# from plyfile import PlyData
# plydata = PlyData.read('Hump_1.ply')
# print('DATA = ', end='')
# print(plydata)
# print('ELE = ', end='')
# print(plydata.elements[1].data)
# exit()

# d = dict()
#
# for j in range(1, 3):
#     d[f'x{j}'] = []
#
# for i in range(1, 10):
#     for j in range(1, 3):
#         d[f'x{j}'].append(i * i + 100 * i)
#
# for p in d:
#     print(d[p])


# import numpy as np
#
# p = ([1, 1, 1],  [2, 2, 2],  [3, 3, 3],  [4, 4, 4])
# q = ([2, 2, 2])
#
# print(f'{np.subtract(p, q)}')
# print(p)

from datetime import datetime

# datetime object containing current date and time
import numpy as np

now = datetime.now()
print("now =", now)

# dd/mm/YY H:M:S
dt_string = now.strftime("%Y%m%d%H%M%S")
print("date and time =", dt_string)

a = np.array([1,2,3])
# x = [{'x1': 1, 'x2': 2}, {'x1': 3, 'x2': 4}, {'x1': 5, 'x2': 6}]
#
# print(', '.join(['%d --> %d' % (e['x1'], e['x2']) for e in x]))


