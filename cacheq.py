# class MemoryCache:
#     def __init__(self):
#         self.cache = {}

#     def add(self, key, value):
#         self.cache[key] = value

#     def get(self, key):
#         return self.cache.get(key)

#     def remove(self, key):
#         if key in self.cache:
#             del self.cache[key]



colors=(10,20,30,40,50,60,70,80,90,100)
x=50
i=1
while (i<len(colors)):
    if (colors[i]==x):
        print("found and the idx is ",i)
    i+=1
    break
    i+=1
else:
    print("not in the list")

