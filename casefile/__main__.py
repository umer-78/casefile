"""python -m casefile bench    the ship gates on synthetic claims, written to results/"""
import sys

from .bench import bench

if __name__ == "__main__":
    if sys.argv[1:] != ["bench"]:
        sys.exit(__doc__)
    print(bench())
