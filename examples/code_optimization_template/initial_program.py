"""Code optimization example for OpenEvolve"""

# EVOLVE-BLOCK-START

# ICPC_1444

n, m = map(int, input().split())
x = [input().strip() for _ in range(n)]


def dfs(i, j, k=0):
    if k == 7:
        return 1
    res = 0
    for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        ni, nj = i + di, j + dj
        if not (0 <= ni < n and 0 <= nj < m):
            continue
        if x[ni][nj] != "YOKOHAMA"[k + 1]:
            continue
        res += dfs(ni, nj, k + 1)
    return res


ans = 0
for i in range(n):
    for j in range(m):
        if x[i][j] == "Y":
            ans += dfs(i, j)

print(ans)


# EVOLVE-BLOCK-END
