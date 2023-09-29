#!/usr/bin/env python

# This script can be used to merge the results for the smaller experiments (to allow parallelizing large experiments)

import pandas as pd
import os 

NUM_SUBSETS = 8 # into how many smaller experiments was the larger experiment divided into
TOTAL_HURRICANES = 100000
EACH_SUBSET_SIZE =  TOTAL_HURRICANES // NUM_SUBSETS
FILENAME_PREFIX = "fig21" # prefix as in "<prefix>_<config>_subset_x_y.csv"
CONFIGS = ['6+6', '6+6+6', 'reconfigurable6+6+6']
FILES_DIR = './outputs/'
RAND_COUNT = 100000
MERGED_OUTPUT_DIR = FILES_DIR

def main():
    final_probs = {}
    subset_ranges = []
    prev_upper = 0

    for i in range(NUM_SUBSETS):
        this_lower_lim = prev_upper + 1
        this_upper_lim = (i+1) * EACH_SUBSET_SIZE
        this_subset = (this_lower_lim, this_upper_lim)
        subset_ranges.append(this_subset)
        prev_upper = this_upper_lim

    all_dfs = {}

    filenames = []
    for config in CONFIGS:
        for subset_num in range(0, NUM_SUBSETS): 
            filenames.append(f"{FILENAME_PREFIX}_{config}_subset_{subset_ranges[subset_num][0]}_{subset_ranges[subset_num][1]}.csv")

    for filename in filenames:
        this_df = pd.read_csv(FILES_DIR + filename)
        all_dfs[filename] = this_df

    for config in CONFIGS:
        probs = {}
        for subset_num in range(0, NUM_SUBSETS):
            filename = f"{FILENAME_PREFIX}_{config}_subset_{subset_ranges[subset_num][0]}_{subset_ranges[subset_num][1]}.csv"
            df = all_dfs[filename]

            probs[subset_ranges[subset_num]] = {
                'green': df.green_probability.values[0],
                'red': df.red_probability.values[0],
                'orange': df.orange_probability.values[0],
                'yellow': df.yellow_probability.values[0],
                'blue': df.blue_probability.values[0],
                'grey': df.grey_probability.values[0],
            }
        
        numerator = {
            'green': 0,
            'red': 0,
            'orange': 0,
            'yellow': 0,
            'blue': 0,
            'grey': 0,
        }

        denominator = {
            'green': 0,
            'red': 0,
            'orange': 0,
            'yellow': 0,
            'blue': 0,
            'grey': 0,
        }

        for subset in probs:
            numerator['green'] += (probs[subset]['green'] * EACH_SUBSET_SIZE * RAND_COUNT)
            numerator['red'] += (probs[subset]['red'] * EACH_SUBSET_SIZE * RAND_COUNT)
            numerator['orange'] += (probs[subset]['orange'] * EACH_SUBSET_SIZE * RAND_COUNT)
            numerator['yellow'] += (probs[subset]['yellow'] * EACH_SUBSET_SIZE * RAND_COUNT)
            numerator['blue'] += (probs[subset]['blue'] * EACH_SUBSET_SIZE * RAND_COUNT)
            numerator['grey'] += (probs[subset]['grey'] * EACH_SUBSET_SIZE * RAND_COUNT)

            denominator['green'] += (EACH_SUBSET_SIZE * RAND_COUNT)
            denominator['red'] += (EACH_SUBSET_SIZE * RAND_COUNT)
            denominator['orange'] += (EACH_SUBSET_SIZE * RAND_COUNT)
            denominator['yellow'] += (EACH_SUBSET_SIZE * RAND_COUNT)
            denominator['blue'] += (EACH_SUBSET_SIZE * RAND_COUNT)
            denominator['grey'] += (EACH_SUBSET_SIZE * RAND_COUNT)

        final_probs[config] = {
            'green': round(numerator['green']/denominator['green'], 3),
            'red': round(numerator['red']/denominator['red'], 3),
            'orange': round(numerator['orange']/denominator['orange'], 3),
            'yellow': round(numerator['yellow']/denominator['yellow'], 3),
            'blue': round(numerator['blue']/denominator['blue'], 3),
            'grey': round(numerator['grey']/denominator['grey'], 3),
        }        

    print(final_probs)

    fn = f"{MERGED_OUTPUT_DIR}{FILENAME_PREFIX}_{config}.csv"
    for c in CONFIGS:
        if not os.path.exists(fn):
            fn_create=open(fn,"w")
            header=",".join(["conf","site_names","hurricane_name","reconf","reconfs_ratio","method","bucket","green_probability","red_probability","orange_probability","yellow_probability","blue_probability","grey_probability"])
            fn_create.write(header+"\n")
            fn_create.close()

        if c==1:
            c="2"
        if c=="1+1":
            c="2-2"
        if c=="6+6":
            c="6-6"

        sn = str(df.site_names.values[0])
        hn = str(df.hurricane_name.values[0])
        m = str(df.method.values[0])
        b = str(df.bucket.values[0])
        r = '1' if c == 'reconfigurable6+6+6' else '0'
        rr = str(0)
        g_prob=str(round(final_probs[c]['green'],3))
        r_prob=str(round(final_probs[c]['red'], 3))
        o_prob=str(round(final_probs[c]['orange'],3))
        y_prob=str(round(final_probs[c]['yellow'],3))
        b_prob=str(round(final_probs[c]['blue'],3))
        gry_prob=str(round(final_probs[c]['grey'],3))
        res=",".join([c,sn,hn,r,rr,m,b,g_prob,r_prob,o_prob,y_prob,b_prob,gry_prob])
        fn_write=open(fn,"a")
        fn_write.write(res+"\n")
        fn_write.close()

if __name__ == '__main__':
    main()
