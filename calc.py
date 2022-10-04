from scipy import asarray as ar
from scipy.stats import skewnorm
import datetime
import time
import sys
import json
from tabulate import tabulate

def playerTime(ptime):
    "Calculate a number of seconds from a HH:MM:SS time"
    t = time.strptime(ptime, '%H:%M:%S')
    return datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min, seconds=t.tm_sec).total_seconds()

def getCurve(times):
    "Given a collection of times in seconds, use all of them greater than 0 to fit a curve that can be used to calculate percentiles"
    ts_arr = ar([t for t in times if t > 0])
    return skewnorm(*skewnorm.fit(ts_arr))

def getTimePercentile(time_sec, curve):
    "Use the survival function of a curve and a time in seconds to calculate a value between 0 and 100, with 100 being the best."
    return 100 * curve.sf(time_sec)

def graphCurve(curve, times, title='Probability Density Function Plot', output_file=None):
    "Create a visualization of a curve produced by getCurve"
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

def calculatePercentiles(race_dict):
    "Calculate percentiles for all players in a dict mapping usernames to times expressed as HH:MM:SS strings, representing one async race"
    ret = {}
    times = [ptime for ptime in race_dict.values() if ptime is not None and ptime != ""]
    if len(times) == 0:
        return ret
    curve = getCurve([playerTime(ptime) for ptime in times])
    for name, ptime in race_dict.items():
        if ptime is not None and ptime != "":
            ret[name] = getTimePercentile(playerTime(ptime), curve)
        else:
            ret[name] = 0
    return ret

def averageRaces(races, default=0):
    "Given a set of races which calculatePercentiles has already been called on, produce a new dictionary giving the average score across all of the races for each username. When a given name is missing from a race, use the default value instead."
    all_keys = set()
    for race in races:
        all_keys = all_keys | set(race.keys())
    ret = {}
    for name in all_keys:
        ret[name] = sum([r.get(name, default) for r in races])/len(races)
    return ret

# if being called directly from the command line with json files describing races, all percentiles and averages (in the future: display as a nice table, also generate graphs of the curves)
if __name__ == "__main__":
    default = 0
    racefiles = sys.argv[1:]
    races = []
    for rf in racefiles:
        with open(rf, 'r') as rfp:
            races.append(json.load(rfp))
    rp = [(racefiles[i], calculatePercentiles(races[i])) for i in range(len(races))]
    average = averageRaces([r[1] for r in rp], default=default)

    headers = ["#", "Player"] + [r[0] for r in rp] + ["Average"]
    sorted_names = sorted(average.keys(), key=lambda x: 100 - average[x])
    table = [[sorted_names.index(name) + 1, name] + [str(round(rp[i][1].get(name, default),3)) + " (" + races[i].get(name, "") + ")" for i in range(len(rp))] + [round(average[name],3)] for name in sorted_names]
    print(tabulate(table, headers=headers))
