from scipy import asarray as ar
from scipy.stats import skewnorm
import datetime
import time
import sys
import json
import pprint

def playerTime(ptime):
    "Calculate a number of seconds from a HH:MM:SS time"
    t = time.strptime(ptime, '%H:%M:%S')
    return datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min, seconds=t.tm_sec).total_seconds()

def getCurve(times):
    ts_arr = ar([t for t in times if t > 0])
    return skewnorm(*skewnorm.fit(ts_arr))

def getTimePercentile(time_sec, curve):
    return 100 * curve.sf(time_sec)

def graphCurve(curve, times, title='Probability Density Function Plot', output_file=None):
    import matplotlib.pyplot as plt
    import matplotlib.ticker as tick
    ts_arr = ar(sorted([t for t in times if t > 0]))
    fix, ax = plt.subplots(1,1)
    ax.xaxis.set_major_formatter(tick.FuncFormatter(lambda x, pos: (datetime.datetime.min + datetime.timedelta(seconds=x)).strftime("%H:%M:%S")))
    ax.plot(ts_arr, curve.pdf(ts_arr), 'r-', lw=5, alpha=0.6, label='PDF')
    ax.hist(ts_arr, density=True, alpha=0.2)
    ax.legend(loc='best', frameon=False)
    plt.title(title)
    if output_file is None:
        plt.show()
    else:
        plt.savefig(output_file)

# calculate totals for one race (dict of usernames -> time strings)
def calculatePercentiles(race_dict):
    times = race_dict.values()
    curve = getCurve([playerTime(ptime) for ptime in times])
    ret = {}
    for name, ptime in race_dict.items():
        ret[name] = getTimePercentile(playerTime(ptime), curve)
    return ret

# average a set of races, given percentile dicts from above
def averageRaces(races):
    all_keys = set()
    for race in races:
        all_keys = all_keys | set(race.keys())
    ret = {}
    for name in all_keys:
        ret[name] = sum([r.get(name, 0) for r in races])/len(races)
    return ret

# if main, generate graphs for each race and output table with all percentiles and averages
if __name__ == "__main__":
    racefiles = sys.argv[1:]
    races = []
    for rf in racefiles:
        with open(rf, 'r') as rfp:
            races.append(json.load(rfp))
    rp = [calculatePercentiles(r) for r in races]
    average = averageRaces(rp)
    pprint.pprint(rp)
    pprint.pprint(average)
