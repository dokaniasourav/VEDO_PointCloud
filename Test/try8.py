
class ABC:
    x = 0


d = ABC()
d.x = 233

setattr(d, 'y', 25)
setattr(d, 'z', 25)

if 'y' in d.__dict__:
    print('YES')

print(d.__dict__)
