#!/usr/bin/env python

from absl import app
from lib.flags import *
from lib.iterators import *
from lib.functions import *
import sys
import traceback

def main(_):
    init_seed()

    post_hurricane_iterator = post_hurricane_instances() # the iterator generates state instances for the system after the hurricane has struck
    cyberattack_iterator = cyberattack_method(info_from_bucket_flag()) # the iterator generates state instances for the system after the cyberattack 
    
    if FLAGS.reconfiguration == 0:
        system_config_iterator = initial_system_config_instances() # the iterator generates state instances for the system's initial state i.e. before both the hurricane and the cyberattack
        f_k_iterator = f_k_values() # the iterator returns the 'f' (byzantine faults) and 'k' (crash faults + proactive recoveries) values for the configuration (e.g. 6+6+6 or 2-2 etc) that the system is in
        combined_entries = combined_table_iterator(post_hurricane_iterator, cyberattack_iterator, system_config_iterator, f_k_iterator) # the iterator for the combined table that includes the system state before the hurricane, after the hurricane, and after the cyberattack.
    
    else: # if reconfiguration is to be done:
        try:
            system_config_iterator = reconfigured_system_config_instances() # the iterator generates the system's states after the reconfiguration
            combined_entries = combined_table_iterator(post_hurricane_iterator, cyberattack_iterator, system_config_iterator, None) # the iterator for the combined table that includes the system state before the hurricane, after the hurricane, and after the cyberattack.
        except Exception as _:
            print("Reconfiguration rules not defined or not found for this configuration. Exiting.")
            sys.exit(1)
        

    # to keep count of states for the instances as colors:
    status_count = {
        "green" : 0,
        "red"   : 0,
        "orange": 0,
        "yellow": 0,
        "blue"  : 0,
        "grey"  : 0
    }

    if FLAGS.save_run_table == 'yes':
        run_table = []
        flush_threshold = 1000000
        init_run_table_file_on_disk()
    
    for combined_table_entry in combined_entries:
        # for each entry in the combined table, (i.e. using the system states before the hurricane, after the hurricane, and after the cyberattack) assign the relevent color to the eventual system state and increment the corresponding counter for it.
        status_color = analyze_instance(combined_table_entry)
        status_count[status_color] += 1
    
        if FLAGS.save_run_table == 'yes':
            run_table_entry = [e for e in combined_table_entry]
            run_table_entry.append(status_color)
            run_table.append(run_table_entry)

            # flush to disk if run_table reaches flush_threshold
            if len(run_table) >= flush_threshold:
                save_run_table(run_table)
                run_table = []

    print_reconfig_stats()
    print_probabilities(status_count)
    
    if FLAGS.save_run_table == 'yes':
        save_run_table(run_table)

if __name__ == '__main__':
    try:
        app.run(main)
        sys.exit(0) # 0 => successful termination
    except SystemExit:
        pass
    except:
        traceback.print_exc()
        sys.exit(1)