data, target = [3, 8, 12, 17, 21, 26, 30, 35], 26
assert data == sorted(data)
lo, hi, steps = 0, len(data) - 1, []
while lo <= hi:
    mid = (lo + hi) // 2
    steps.append((lo, hi, mid, data[mid]))
    if data[mid] == target: break
    if data[mid] < target: lo = mid + 1
    else: hi = mid - 1
for s in steps: print("lo=%d hi=%d mid=%d value=%d" % s)
print("found at index", steps[-1][2], "in", len(steps), "steps;", "linear search would take", data.index(target) + 1)
