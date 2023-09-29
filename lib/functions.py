from lib.flags import *
from copy import deepcopy
import os
from collections import Counter

reconf_rat = 0 # init value

def info_from_bucket_flag():
    """
    The function, based on the 'bucket', 'site_prob'. and 'server_prob' flags, returns the site and server failure probabilities and whether the cyberattack taking place is supposed to isolate a site, down a server, or both.

    :return: SITE_PROB, SERVER_PROB, sites, servers
    """ 

    SITE_PROB = FLAGS.site_prob
    SERVER_PROB = FLAGS.server_prob
    if FLAGS.bucket == 1:
        SITE_PROB = 0
        SERVER_PROB = 0
        sites = 0
        servers = 0
    elif FLAGS.bucket == 2:
        SITE_PROB = 0
        sites = 0
        servers = 1
    elif FLAGS.bucket == 3:
        SERVER_PROB = 0
        sites = 1
        servers = 0
    elif FLAGS.bucket == 4:
        sites = 1
        servers = 1
    else:
        print("invalid bucket parameter given")
        quit()
    
    return SITE_PROB, SERVER_PROB, sites, servers

def get_op_state(config, state, intrusions, f, k, is_OOB):
    '''
    returns operational state of config with state = 'state'
    '''
    if len(config) > 2 and int(FLAGS.num_CCs) >= 3:
        return op_state_general(state, intrusions, f, k, is_OOB)
    elif len(config) > 2:
        return op_state_spire(state, intrusions, f, k)
    elif len(config) == 2:
        return op_state_spire_pb(state, intrusions, f, k)
    else:
        return op_state_spire_1CC(state, intrusions, f, k)

def op_state_spire_1CC(state, intrusions, f, k):
    if len(intrusions) > f:
        return 'grey'

    available_replicas = state[0]

    if available_replicas > 2*f+k+1:
        return 'green'
    elif available_replicas == 2*f+k+1:
        return 'yellow'
    else:
        return 'red'

def op_state_spire(state, intrusions, f, k):
    #print(intrusions)
    if len(intrusions) > f:
        return 'grey'

    if state[0] == 0 and state[1] == 0: # no CC replicas left
        return 'red'

    available_replicas, available_cc_replicas = 0,0
    #print(state)
    for i in range(len(state)):
        if i <= 1:
            #state[i] -= intrusions.count('CC'+str(i+1))
            available_cc_replicas += state[i]
        #else:
            #state[i] -= intrusions.count('DC'+str(i-1))
        available_replicas += state[i]

    if available_cc_replicas <= 0 or available_replicas < 2*f+k+1:
        return 'red'
    elif available_replicas == 2*f+k+1:
        return 'yellow'
    elif available_cc_replicas == 1:
        return 'blue'
    else:
        return 'green'

def op_state_spire_pb(state, intrusions, f, k):
    if len(intrusions) > f:
        return 'grey'

    available_replicas_primary = state[0]
    available_replicas_backup = state[1]

    if available_replicas_primary > 2*f+k+1:
        return 'green'
    elif available_replicas_primary == 2*f+k+1:
        return 'yellow'
    elif available_replicas_backup >= 2*f+k+1: # if primary_backup and switching to backup
        return 'orange'
    else:
        return 'red'

def op_state_general(state, intrusions, f, k, is_OOB):
    #print(intrusions)
    if len(intrusions) > f:
        return 'grey'

    no_replicas_in_this_CC = []
    for i in range(int(FLAGS.num_CCs)):
        if state[i] == 0:
            no_replicas_in_this_CC.append(True)
        else:
            no_replicas_in_this_CC.append(False)
    if all(no_replicas_in_this_CC): # no available replicas in CCs
        return 'red'
    
    available_replicas, available_cc_replicas = 0,0
    #print(state)
    for i in range(len(state)):
        if i < int(FLAGS.num_CCs):
            #state[i] -= intrusions.count('CC'+str(i+1))
            available_cc_replicas += state[i]
        #else:
            #state[i] -= intrusions.count('DC'+str(i-1))
        available_replicas += state[i]

    if available_cc_replicas <= 0 or available_replicas < 2*f+k+1:
        return 'red'
    elif available_replicas == 2*f+k+1:
        return 'yellow'
    elif available_cc_replicas == 1:
        return 'blue'
    else:
        return 'green'

def get_siteNames_and_hurr(input_file_name):
    hurr_filename=input_file_name.split("/")[-1]
    hurr_filename=hurr_filename.split(".")[0]
    hurr_filename=hurr_filename.split("_")
    hn=hurr_filename[0]+"_"+hurr_filename[1]
    #TODO:Taking only 3 site names, fix this to be dynamic
    sn="+".join(hurr_filename[2:5])
    return sn,hn

def get_method_name(n):
    if n==1:
        return "worst"
    if n==2:
        return "random"
    if n==3:
        if FLAGS.server_threshold==0:
            return "Probabilistic+NT"
        return "Probabilistic+"+FLAGS.server_threshold
    return "Invalid Attacker Power"

def get_bucket_name(n):
    if n==1:
        return "NoAttack"
    if n==2:
        return "ServerIntru."
    if n==3:
        return "Site Iso."
    if n==4:
        return "Site+Server"

def print_probabilities(status_count):
    total_instances = status_count["green"] + status_count["red"] + status_count["orange"] + status_count["yellow"] + status_count["blue"] + status_count["grey"]
    p_green = status_count["green"]/total_instances
    p_red = status_count["red"]/total_instances
    p_orange = status_count["orange"]/total_instances
    p_yellow = status_count["yellow"]/total_instances
    p_blue = status_count["blue"]/total_instances
    p_grey = status_count["grey"]/total_instances

    if(FLAGS.simple_print == 'yes'):
        print(round(p_green,7))
        print(round(p_red, 7))
        print(round(p_orange,7))
        print(round(p_yellow,7))
        print(round(p_blue,7))
        print(round(p_grey,7))
    else:
        print('Results:')
        print('Probability of green = ', round(p_green,7))
        print('Probability of red = ', round(p_red, 7))
        print('Probability of orange = ', round(p_orange,7))
        print('Probability of yellow = ', round(p_yellow,7))
        print('Probability of blue = ', round(p_blue,7))
        print('Probability of grey = ', round(p_grey,7))
    
    #conf,site_names,hurricane_name,method,bucket,reconf,reconfs_ratio,green_probability,red_probability,orange_probability,yellow_probability,blue_probability,grey_probability
    if FLAGS.output_write_to_file == 'yes':
        fn=FLAGS.output_file
        if not os.path.exists(fn):
            fn_create=open(fn,"w")
            header=",".join(["conf","site_names","hurricane_name","reconf","reconfs_ratio","method","bucket","green_probability","red_probability","orange_probability","yellow_probability","blue_probability","grey_probability"])
            fn_create.write(header+"\n")
            fn_create.close()

        c=FLAGS.configuration
        if c==1:
            c="2"
        if c=="1+1":
            c="2-2"
        if c=="6+6":
            c="6-6"
        sn,hn=get_siteNames_and_hurr(FLAGS.input_file)
        m=get_method_name(FLAGS.method)
        b=get_bucket_name(FLAGS.bucket)
        r=str(FLAGS.reconfiguration)
        rr=str(round(reconf_rat,7))
        g_prob=str(round(p_green,7))
        r_prob=str(round(p_red, 7))
        o_prob=str(round(p_orange,7))
        y_prob=str(round(p_yellow,7))
        b_prob=str(round(p_blue,7))
        gry_prob=str(round(p_grey,7))
        res=",".join([c,sn,hn,r,rr,m,b,g_prob,r_prob,o_prob,y_prob,b_prob,gry_prob])
        fn_write=open(fn,"a")
        fn_write.write(res+"\n")
        fn_write.close()

def analyze_instance(combined_table_entry): # basically identical to instance_analysis function from the original code. just runs the loop one time
    # row := 
    #   [0] = hurricane_result, 
    #   [1] = cyberattack_result, 
    #   [2] = state, 
    #   [3] = intrusion, 
    #   [4] = isolation, 
    #   [5] = post-reconfig, 
    #   [6] = [f, k], 
    #   [7] = isOOB
    combined_table = [combined_table_entry] 
    i = 0

    config = combined_table[i][5]
    state = combined_table[i][2]
    f = combined_table[i][6][0]
    k = combined_table[i][6][1]
    hurricane_outcome = deepcopy(combined_table[i][0])
    is_OOB = combined_table_entry[7]

    # COMBINE STATE AND CONFIG
    site2state = {}
    if len(FLAGS.configuration) == 1: # only CC1 has machines available
        site2state['CC1'] = state[0]
        config_state = [state[0]]
    elif len(config) == 1:
        if FLAGS.events_sequence in [1,2] and FLAGS.method == 1:
            config_state = [state[0]]
        elif FLAGS.events_sequence in [2] and FLAGS.method in [2,3]:
            for x in state:
                if x != 0:
                    config_state = [x]
                    break
        else: 
            if state[0] >= state[1]:
                site2state['CC1'] = state[0]
            else:
                site2state['CC2'] = state[1]
            config_state = [max(state[0],state[1])]
    elif len(config) == 2:
        if int(FLAGS.num_CCs) <= 2 or int(FLAGS.reconfiguration) == 0 or (int(FLAGS.events_sequence) in [1] and int(FLAGS.method) in [1]):
            site2state['CC1'] = state[0]
            site2state['CC2'] = state[1]
            config_state = [state[0],state[1]]
        else:
            if int(FLAGS.events_sequence) in [1]: # H->R->CA
                non_flooded_ccs = []
                for x in range(len(hurricane_outcome)):
                    if hurricane_outcome[x] != 0:
                        non_flooded_ccs.append(f'CC{x+1}')
                config_state = []
                for cc in non_flooded_ccs:
                    idx = int(cc[2:]) - 1
                    site2state[cc] = state[idx]
                    config_state.append(state[idx])
            else:   # H+CA->R
                up_ccs = []
                for x in range(len(state)):
                    if state[x] != 0:
                        up_ccs.append(f'CC{x+1}')
                config_state = []
                for cc in up_ccs:
                    idx = int(cc[2:]) - 1
                    site2state[cc] = state[idx]
                    config_state.append(state[idx])

    elif len(config) > 2:
        site2state['CC1'] = state[0]
        site2state['CC2'] = state[1]
        config_state = [state[0],state[1]] # definitely using both control centers
        hurricane_outcome[0] = 0 # both CCs already taken
        hurricane_outcome[1] = 0
        for j in range(2,len(config)): # choose data centers based on hurricane outcome
            index = hurricane_outcome[2:].index(max(hurricane_outcome[2:]))
            index+=2
            site2state['DC'+str(index-1)] = state[index]
            config_state += [state[index]] # take the DC
            hurricane_outcome[index] = 0               # disallow the DC to be taken multiple times

    intrusions = combined_table[i][3]
    isolations = combined_table[i][4]
    hurricane_outcome = deepcopy(combined_table[i][0])

    # don't count intrusions at downed sites
    valid_intrusions = []
    for intrusion in intrusions:
        site_idx = -1
        if 'CC' in intrusion:
            site_idx = int(intrusion[2]) - 1
        else:
            site_idx = int(intrusion[2]) + 1
        if not (intrusion not in site2state or hurricane_outcome[site_idx] == 0):
            valid_intrusions.append(intrusion)
    
    status = get_op_state(config, config_state, valid_intrusions, f, k, is_OOB) # get the status functions

    if status == 'yellow' and (config == [2,2] or config == [2]): # correct yellow results for non-intrusion tolerant architectures
        status = 'green'

    if is_OOB is not None:
        if is_OOB and status == 'green':
            status = 'orange'

    return status

def print_reconfig_stats():
    from lib.iterators import reconfigured_system_config_instances as reconf_insts
    if(FLAGS.simple_print == "yes"):
            print(reconf_insts.reconfig_counter/(reconf_insts.reconfig_counter + reconf_insts.noreconfig_counter))
    else:
        print("Number of reconfigurations = ", reconf_insts.reconfig_counter)
        print("% time reconfiguring = ", end='')
        try:
            print(reconf_insts.reconfig_counter/(reconf_insts.reconfig_counter + reconf_insts.noreconfig_counter))
        except ZeroDivisionError:
            print("0")

def site2status_dict(configuration):
    site2status = {}

    dc_counter = 1
    for idx, _ in enumerate(configuration):
        if idx < FLAGS.num_CCs:
            site2status['CC'+str(idx+1)] = configuration[idx]
        else:
            site2status['DC'+str(dc_counter)] = configuration[idx]
            dc_counter += 1

    return site2status

def init_run_table_file_on_disk():
    from pandas import DataFrame
    df = DataFrame()
    dir_path = "./run_tables/"
    filename = FLAGS.input_file
    filename = filename.split('/')[-1]
    filename = dir_path + FLAGS.configuration + "_method_" + str(FLAGS.method) + "_reconfiguration_" + str(FLAGS.reconfiguration) + "_bucket_" + str(FLAGS.bucket) + "_" + filename 
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    df.to_csv(filename, encoding='utf-8', index=False, mode='w')

def save_run_table(run_table):

    # row := hurricane_result, cyberattack_result, state, intrusion, isolation, post-reconfig, f_k, isOOB, color-state
     
    from pandas import DataFrame

    df2 = DataFrame(run_table)
    dir_path = "./run_tables/"
    filename = FLAGS.input_file
    filename = filename.split('/')[-1]
    filename = dir_path + FLAGS.configuration + "_method_" + str(FLAGS.method) + "_reconfiguration_" + str(FLAGS.reconfiguration) + "_bucket_" + str(FLAGS.bucket) + "_" + filename 
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    df2.to_csv(filename, encoding='utf-8', index=False, mode='a')

def parse_subset_flag():
    return_dict = {}

    if FLAGS.hurricane_subset == 'all':
        return_dict['lower_limit'] = 1
        return_dict['upper_limit'] = int(FLAGS.num_hurricane_instances)
    else:
        lower = int(FLAGS.hurricane_subset[1:-1].split(',')[0])
        upper = int(FLAGS.hurricane_subset[1:-1].split(',')[1])
        return_dict['lower_limit'] = lower
        return_dict['upper_limit'] = upper
    
    return return_dict
