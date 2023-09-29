from lib.flags import *
import random
import numpy as np
from copy import deepcopy
from lib.functions import site2status_dict, info_from_bucket_flag, parse_subset_flag


def init_seed():
    random.seed(FLAGS.seed)

class hurricane_instances:
    """ Class to implement an iterator for hurricane instances read from input_file """
    
    def read_hurricane_data(self):
        """ Reads hurricane impact data from input_file and returns a pandas dataframe """
        from pandas import read_csv
        hurricane_instances = read_csv(FLAGS.input_file)
        hurricane_instances = hurricane_instances.transpose()
        return hurricane_instances

    def __init__(self):
        self.hurricane_data = self.read_hurricane_data()
        self.total_hurricanes = self.hurricane_data.shape[0]
        self.curr_hurr_num = 1 # number 0 is just column heading: CC1, CC2, DC1, DC2, DC3

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr_hurr_num <= self.total_hurricanes - 1:
            this_hurricane_instance = self.hurricane_data.iloc[self.curr_hurr_num]
            self.curr_hurr_num += 1
            return this_hurricane_instance
        else:
            raise StopIteration

class initial_system_config_instances:
    """ Class to implement an iterator for replicas based on given configuration (represents initial, fully-functional system) """
    # Based on initialize_table function in the original code. this iterators returns an element of "config_table" from the original code
    def __init__(self):
        self.curr = 1
        self.limit = FLAGS.num_hurricane_instances
        configuration = FLAGS.configuration
        self.config_split = configuration.split('+')

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr <= self.limit:
            self.curr += 1

            entry = []
            for site in self.config_split:
                entry.append(int(site))
            
            return entry
        else:
            raise StopIteration
    
    def reset(self):
        self.__init__()

class post_hurricane_instances:
    """ Class to implement an iterator for the results of every hurricane instance. 1 in hurricane instance means site is flooded (# of replicas set to 0)"""
    # Based on run_hurricane function in the original code
    def __init__(self):
        self.curr = parse_subset_flag()['lower_limit']
        self.limit = parse_subset_flag()['upper_limit']
        self.hurricane_insts = hurricane_instances()
        self.config_table_insts = initial_system_config_instances()

        # move iterator to the right place. Used when a subset of hurricanes are being used to run experiments (i.e. using hurricane_subset flag):
        for _ in range(0, parse_subset_flag()['lower_limit'] - 1):
            next(self.hurricane_insts)
            next(self.config_table_insts)

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr <= self.limit:
            self.curr += 1
            this_hurricane_instance = next(self.hurricane_insts)
            this_system_config = next(self.config_table_insts)
            this_post_hurr_system_config = [i for i in this_system_config] # initialize as a copy of this_system_config

            for i in range(len(this_system_config)):
                if this_hurricane_instance[i] == 1:
                    this_post_hurr_system_config[i] = 0
                
            return this_post_hurr_system_config
        else:
            raise StopIteration
    
    def reset(self):
        self.__init__()

class reconfigured_system_config_instances:
    """ returns system state after it is been reconfigured to the new state as defined in the file FLAGS.reconf_rules """
    reconfig_counter = 0
    noreconfig_counter = 0

    def read_reconf_rules(self, reconf_rules_filename):

        reconf_rules = {}   # dict[key1][key2] = value

        # read and extract lines from file
        reconf_rules_file = open(reconf_rules_filename, 'r')
        reconf_rules_lines = reconf_rules_file.readlines()

        for line in reconf_rules_lines:

            line = line.strip()     # remove trailing white spaces
            line_list = line.split(';')

            # There must be exactly 3 parts in each line (key1, list of key2, and value)
            if len(line_list) == 3:

                # We first clean key1
                key1 = line_list[0]
                key1 = key1.strip()     # remove trailing white spaces
                key1 = key1.replace('(','').replace(')','')     # remove parenthesis
                key1 = key1.replace(' ','')     # remove spaces

                # Check if key1 already exists or not
                if key1 not in reconf_rules.keys():
                    reconf_rules[key1] = {}

                # Next, we extract and clean the list of key2
                key2_list = line_list[1]
                key2_list = key2_list.strip()     # remove trailing white spaces
                key2_list = key2_list.replace('[','').replace(']','')   #remove brackets
                key2_list = key2_list.split(',')

                for key2 in key2_list:
                    key2 = key2.strip()     # remove trailing white spaces
                    key2 = key2.replace('(','').replace(')','')     # remove parenthesis

                    # Check if key2 already exists or not
                    if key2 not in reconf_rules[key1].keys():
                        value = line_list[2]
                        value = value.strip()     # remove trailing white spaces
                        value = value.replace('(','').replace(')','')     # remove parenthesis
                        value = value.replace(' ', '')    # remove white spaces
                        reconf_rules[key1][key2] = value
        
        # We are done, so return the resultant dictionary
        return reconf_rules

    def reconf_rules_key1(self, f, k, conf):
        return "f="+str(f)+",k="+str(k)+","+"+".join([str(x) for x in conf])

    def reconf_rules_key2(self, conf):
        return "+".join([str(x) for x in conf])

    def get_reconfiguration(self, f, k, configuration, post_hurricane, reconfig_rules):
        res_dict = {}
        key1 = self.reconf_rules_key1(f,k,configuration)
        key2 = self.reconf_rules_key2(post_hurricane)
        res = reconfig_rules[key1][key2]
        res = res.split(',')
        res_dict["f"] = int(res[0].split('=')[1])
        res_dict["k"] = int(res[1].split('=')[1])
        if '+' in res[2]:
            res_dict["configuration"] = [int(x) for x in res[2].split('+')]
        else:
            res_dict["configuration"] = [int(x) for x in res[2].split('-')]
        return res_dict

    def check_if_OOB(self, pre, post):
        if FLAGS.events_sequence == 0:
            is_OOB = False
        elif FLAGS.events_sequence in [1, 2]:
            num_available_replicas = sum(post)
            if num_available_replicas >= ((2 * FLAGS.f) + FLAGS.k + 1):
                is_OOB = False
            else:
                is_OOB = True
        return is_OOB

    def config_without_intrusions(self, config):
        config_without_intrusions = []
        init_config = self.config_split
        index = 0
        for site in config:
            if site == 0:
                config_without_intrusions.append(site)
            else:
                config_without_intrusions.append(int(init_config[index]))
            index += 1
        return config_without_intrusions

    def __init__(self, context='call_from_main', pre_generated_attacks_list=None):
        self.context = context
        self.index_for_hurricane_instances = 0
        if self.context == 'call_from_combined_table_method_2/3':
            self.pre_generated_attacks = pre_generated_attacks_list 
            self.index_for_pre_generated_attacks = 0
        self.curr = 0
        self.limit = FLAGS.num_hurricane_instances
        configuration = FLAGS.configuration
        self.config_split = configuration.split('+')
        self.reconfig_rules = self.read_reconf_rules(FLAGS.reconf_rules)
        self.post_hurricane_iterator = post_hurricane_instances()
        self.base_config_iterator = initial_system_config_instances() # base config = config without reconfiguration
        if FLAGS.events_sequence == 2:
            site_prob, server_prob, sites, servers = info_from_bucket_flag()
            if FLAGS.method == 1:
                self.post_CA_iterator = worst_cyberattack_instances(sites, servers) # FLAGS.hurricane_knowledge handled inside the class
            elif FLAGS.method == 2:
                self.post_CA_iterator = random_cyberattack_instances(sites, servers)
            elif FLAGS.method == 3:
                self.post_CA_iterator = probabilistic_cyberattack(site_prob, server_prob)
            self.post_CA_iterator_copy = deepcopy(self.post_CA_iterator)
        self.move_on_to_next_hurricane = True
        self.current_hurricane = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr < self.limit:
            # self.curr += 1
            
            pre_hurricane_sites = []
            for site in self.config_split:
                pre_hurricane_sites.append(int(site))
            
            if FLAGS.events_sequence in [0,1]: 
                self.curr += 1
                post_hurricane_sites = next(self.post_hurricane_iterator)
            else:
                if self.move_on_to_next_hurricane == True:
                    self.curr += 1
                    post_hurricane_sites = next(self.post_hurricane_iterator)
                    self.move_on_to_next_hurricane = False
                    self.current_hurricane = post_hurricane_sites
                else:
                    post_hurricane_sites = self.current_hurricane

            if FLAGS.events_sequence == 0:  # premptive reconfiguration based on Hurricane impact knowledge -then-> Hurricane -then-> CA
                sites_right_before_reconfig = post_hurricane_sites
            elif FLAGS.events_sequence == 1: # CA in the aftermath of hurricane
                sites_right_before_reconfig = post_hurricane_sites
            elif FLAGS.events_sequence == 2: # CA coincide with hurricane
                if FLAGS.method == 1:
                    this_cyberattack_result, intrusion_instance, isolation_instance = next(self.post_CA_iterator)
                    combined_CA_and_post_hurricane = this_cyberattack_result
                else:
                    this_cyberattack_result = self.pre_generated_attacks[self.index_for_pre_generated_attacks][0]
                    intrusion_instance = self.pre_generated_attacks[self.index_for_pre_generated_attacks][1]
                    isolation_instance = self.pre_generated_attacks[self.index_for_pre_generated_attacks][2]
                    self.index_for_pre_generated_attacks += 1
                    if not (self.index_for_pre_generated_attacks < len(self.pre_generated_attacks)):
                        self.index_for_pre_generated_attacks = 0
                        self.index_for_hurricane_instances += 1
                        self.move_on_to_next_hurricane = True
                        self.curr = 0
                        self.base_config_iterator.reset()

                    combined_CA_and_post_hurricane = []
                    for idx in range(len(this_cyberattack_result)):
                        combined_CA_and_post_hurricane.append(min(post_hurricane_sites[idx], this_cyberattack_result[idx]))
                sites_right_before_reconfig = self.config_without_intrusions(combined_CA_and_post_hurricane)# reconfiguration process does not take intrusions into account because we are going with the model where site isolations are detectable but server intrusions are not

            # IB or OOB:
            is_OOB = self.check_if_OOB(pre_hurricane_sites, sites_right_before_reconfig)

            rules_res = self.get_reconfiguration(FLAGS.f, FLAGS.k, pre_hurricane_sites, sites_right_before_reconfig, self.reconfig_rules)
            reconfig = rules_res['configuration']

            init_config = [int(x) for x in self.config_split]
            if reconfig == init_config: # i.e. no reconfiguration took place
                reconfig = sites_right_before_reconfig
            
            f_k = [rules_res['f']] + [rules_res['k']]
            f_k_iterator = f_k_values(is_reconfig_case=True, f_val=f_k[0], k_val=f_k[1])

            if self.context == 'call_from_main':
                this_base_config = next(self.base_config_iterator)
                if reconfig == this_base_config: # compare to the config if reconfiguration did not happen
                    reconfigured_system_config_instances.noreconfig_counter += 1
                else:
                    reconfigured_system_config_instances.reconfig_counter += 1

            return reconfig, f_k_iterator, is_OOB
        else:
            raise StopIteration

class f_k_values:
    """ Returns the f and k values for the given configuration as follows (f, k)"""
    
    def __init__(self, **kwargs):
        self.curr = 0
        self.limit = FLAGS.num_hurricane_instances
        self.is_reconfig_case = kwargs.get('is_reconfig_case', False)
        if self.is_reconfig_case:
            self.f_val = kwargs.get('f_val', None)
            self.k_val = kwargs.get('k_val', None)
            self.limit = 0 # in the case of reconfiguration, this iterator runs once for each reconfiguration state.

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr <= self.limit:
            self.curr += 1
            
            this_f_k_val = []
            if FLAGS.reconfiguration == 1 and self.is_reconfig_case:
                this_f_k_val = [self.f_val, self.k_val]
            elif FLAGS.reconfiguration == 0:
                this_f_k_val = [FLAGS.f, FLAGS.k]

            return this_f_k_val
        else:
            raise StopIteration

class _random_no_attack:
    """ attack for method == 2 and bucket == 1 """
    
    def __init__(self, site2status, count):
        self.curr = 0
        self.count = count
        self.site2status = site2status

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr < self.count:
            self.curr += 1
            return list(self.site2status.values()), [], []
        else:
            raise StopIteration

class _random_server_down_attack:
    """ attack for method == 2 and bucket == 2 """
    
    def __init__(self, site2status, count, server_threshold):
        self.curr = 0
        self.count = count
        self.server_threshold = server_threshold
        self.initial_conf = list(site2status.values())
        self.sites = list(site2status.keys())
        self.random = random.Random(FLAGS.seed)

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr < self.count:
            self.curr += 1
            
            instance = self.initial_conf.copy()
            instance_servers=[]
            while len(instance_servers) < self.server_threshold:
                # rand=random.randint(0, 10*self.count) % len(instance)
                rand = self.random.randint(0, 10*self.count) % len(instance)
                if(instance[rand]>0):
                    instance[rand]-=1
                    instance_servers.append(self.sites[rand])

            return instance, instance_servers, []
        else:
            raise StopIteration

class _random_site_isolation_attack:
    """ attack for method == 2 and bucket == 3 """
    
    def __init__(self, site2status, count, sites_threshold):
        self.curr = 0
        self.count = count
        self.sites_threshold = sites_threshold
        self.initial_conf=list(site2status.values())
        self.sites=list(site2status.keys())
        self.random = random.Random(int(FLAGS.seed)+1)

    def __iter__(self):
        return self

    def __next__(self):
        if self.curr < self.count:
            self.curr += 1
            instance=self.initial_conf.copy()
            instance_sites=[]
            while len(instance_sites) < self.sites_threshold:
                # rand=random.randint(0, 10*self.count) % len(instance)
                rand = self.random.randint(0, 10*self.count) % len(instance)
                if(instance[rand]!=0):
                    instance[rand]=0
                    instance_sites.append(self.sites[rand])
            
            return instance, [], instance_sites
        else:
            raise StopIteration

class _random_combined_attacks:
    """ attack for method == 2 and bucket == 4 """
    def combine_attacks(self, cyberattack_table1_instance, cyberattack_table2_instance):
        cyberattack_table1 = [cyberattack_table1_instance]
        cyberattack_table2 = [cyberattack_table2_instance]
        final_cyberattack_table = []
        for i in range(len(cyberattack_table1)):
            new_entry = []
            for j in range(len(cyberattack_table1[i])):
                new_entry.append(min(cyberattack_table1[i][j], cyberattack_table2[i][j]))
            final_cyberattack_table.append(new_entry)

        return final_cyberattack_table

    def __init__(self, site2status, count, server_threshold, sites_threshold):
        self.server_down_attack = _random_server_down_attack(site2status, count, server_threshold)
        self.site_isolation_attack = _random_site_isolation_attack(site2status, count, sites_threshold)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            random_cyber_attacks1, random_attack_servers, _ = next(self.server_down_attack)
            random_cyber_attacks2, _, random_attack_sites = next(self.site_isolation_attack)
            random_cyber_attacks = self.combine_attacks(random_cyber_attacks1, random_cyber_attacks2)
            return random_cyber_attacks[0], random_attack_servers, random_attack_sites
        except StopIteration:
            raise StopIteration

class random_cyberattack_instances:
    """ Instances for method 2
        
        Returns on each iteration:
        Current status of configuration after cyber attack
        sites per each server intrusion
        site isolations """
    # based on apply_random_cyberattack from the original code
    
    def __init__(self, sites, servers):
        self.sites = sites
        self.servers = servers
        self.count = int(FLAGS.random_count)
        self.server_threshold = int(FLAGS.server_threshold)
        self.sites_threshold = int(FLAGS.sites_threshold)
        self.initial_config = FLAGS.configuration # for all the three reconf_strategies 'preemptive', 'post_hurricane', 'post_CA'
        self.initial_config = self.initial_config.split('+')
        self.initial_config = [int(x) for x in self.initial_config]
        self.site2status = site2status_dict(self.initial_config)
        
        if self.sites == 0 and self.servers == 0:
            self.this_attack = _random_no_attack(self.site2status, self.count)
        elif self.sites == 0 and self.servers == 1:
            self.this_attack = _random_server_down_attack(self.site2status, self.count, self.server_threshold)
        elif self.sites == 1 and self.servers == 0:
            self.this_attack = _random_site_isolation_attack(self.site2status, self.count, self.sites_threshold)
        elif self.sites == 1 and self.servers == 1:
            self.this_attack = _random_combined_attacks(self.site2status, self.count, self.server_threshold, self.sites_threshold)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.this_attack)
        except StopIteration:
            raise StopIteration

class worst_cyberattack_instances:
    """ returns the worst-case cyberattack instances as defined in the documentation """
    # based on apply_cyberattack function from the original code. applies cyberattack to config_table (post hurricane)
    
    def worst_case(self, site2status, intrusions, disconnections): # worst case cyberattack
        if intrusions > FLAGS.f: # try to get gray first
            site2status, intrusion_list = self.worst_case_intrude(site2status, intrusions)
            site2status, isolation_list = self.worst_case_isolate(site2status, disconnections)
        else: # try isolations first
            site2status, isolation_list = self.worst_case_isolate(site2status, disconnections)
            site2status, intrusion_list = self.worst_case_intrude(site2status, intrusions)

        return site2status, intrusion_list, isolation_list

    def worst_case_isolate(self, site2status, disconnections): # isolate a given number of sites targeting CC1 over CC2 and CCs over DCs
        isolation_list = []
        for disconnection in range(disconnections):
            target = ''
            num_replicas = 0
            for site in site2status: # pick a target site, prioritize working sites, then CCs, then highest replica sites
                if 'CC' in site:
                    if site2status[site] > num_replicas:
                        target = site
                        num_replicas = site2status[site]
                if 'DC' in site:
                    if 'CC' in target:
                        continue
                    if site2status[site] > num_replicas:
                        target = site
                        num_replicas = site2status[site]
            if target == '':
                continue

            site2status[target] = 0 # disconnect

            isolation_list.append(target)

        return site2status, isolation_list

    def worst_case_intrude(self, site2status, intrusions): # worst case intrusion. Attacks CC1 before CC2 before DCs provided the targeted site still has functional replicas
        intrusion_list = []
        for intrusion in range(intrusions):
            target = ''
            for site in site2status:
                if site2status[site]-intrusion_list.count(site) > 0: # go after first possible site with working replicas since CCs come before DCs in the dictionary
                    target = site
                    break
            if target == '':
                continue
            intrusion_list.append(target)
            site2status[target] -= 1

        return site2status, intrusion_list

    def __init__(self, sites, servers):
        self.disconnections = sites
        self.intrusions = servers

        if FLAGS.events_sequence == 0:
            if FLAGS.hurricane_knowledge == 'no':
                self.config = initial_system_config_instances()
            else:
                self.config = post_hurricane_instances()
        elif FLAGS.events_sequence == 1:
            # the attacker has to have the hurricane knowledge in this case
            if FLAGS.reconfiguration == 0:
                self.config = post_hurricane_instances()
            else:
                self.config = reconfigured_system_config_instances(context='call_from_worst_CA_class') # post_reconfig_instances are based on hurricane impact
        elif FLAGS.events_sequence == 2:
            # the attacker has to have the hurricane knowledge in this case
            self.config = post_hurricane_instances()

    def __iter__(self):
        return self

    def __next__(self):
        try:
            if FLAGS.events_sequence == 1:
                if FLAGS.reconfiguration == 0:
                    this_system_config = next(self.config)
                else:
                    this_system_config, _, _ = next(self.config)
            else:
                this_system_config = next(self.config)

            # create dictionary mapping sites to statuses
            site2status = site2status_dict(this_system_config)
        
            # what if we only want to use DC2 for example? -> this wouldn't happen pre-cyberattack

            # run method # TODO: any change in attack logic because of reconf knowledge. (for 6+6+6 with s=1 f=1 the current algorithm should still be the worst case attack (isolate first available site then 1 intrusion separately))
            site2status, intrusion_list, isolation_list = self.worst_case(site2status, self.intrusions, self.disconnections)
            intrusion_result = intrusion_list
            isolation_result = isolation_list
            new_state = []
            for site in site2status:
                new_state.append(site2status[site])
            cyberattack_result = new_state
            return cyberattack_result, intrusion_result, isolation_result

        except StopIteration:
            raise StopIteration

class probabilistic_cyberattack:
    """ returns the probabilistic cyberattack instances as defined in the documentation """
    # based on apply_probabilistic_cyberattack function from the original code.

    def get_worst_sites(self, curr_ca_sites,site2status):
        import operator
        choice_sites={}
        for (id,site) in curr_ca_sites:
            choice_sites[(id,site)]=site2status[site]
        sorted_choice_sites=dict( sorted(choice_sites.items(), key=operator.itemgetter(1),reverse=True))
        return(list(sorted_choice_sites.keys()))

    def attack_with_threshold_random(self, attack_servers,attack_sites,server_threshold,sites_threshold):
        #Choose sites , if less than threshold get all. If more than threshold choose random sites from chances
        threshold_attack_sites=[]
        for curr_ca_sites in attack_sites:
            if len(curr_ca_sites)<=sites_threshold:
                threshold_attack_sites.append(curr_ca_sites)
            else:
                self.random.shuffle(curr_ca_sites)
                threshold_attack_sites.append(curr_ca_sites[:sites_threshold])
        #Choose servers , if less than threshold get all. If more than threshold choose random servers from chances
        #Since it is random, we dont check the servers choosen are from isolated sites or not
        threshold_attack_servers=[]
        for curr_ca_servers in attack_servers:
            if len(curr_ca_servers)<=server_threshold:
                threshold_attack_servers.append(curr_ca_servers)
            else:
                self.random.shuffle(curr_ca_servers)
                threshold_attack_servers.append(curr_ca_servers[:server_threshold])

        return threshold_attack_servers,threshold_attack_sites

    def attack_with_threshold_worst(self, attack_servers,attack_sites,server_threshold,sites_threshold,initial_config,site2status):
        #Choose sites , if less than threshold get all. If more than threshold choose worst from chances
        # Worst sites in priority order 1. Site is maximum replicas, 2. CC if up 3. rest of up sites
        threshold_attack_sites=[]
        curr_ca_sites = attack_sites[0]
        if len(curr_ca_sites)<=sites_threshold:
            threshold_attack_sites.append(curr_ca_sites)
        else:
            #sort sites in above priority order
            sorted_sites=self.get_worst_sites(curr_ca_sites,site2status)
            threshold_attack_sites.append(sorted_sites[:sites_threshold])
        
        #Choose servers , if less than threshold get all. If more than threshold choose random worst from chances
        #Server priority order 1. Not from isolated site , 2. CC first preference, 3. any up site
        threshold_attack_servers=[]
        i=0
        curr_ca_servers = attack_servers[0]
        #As this is worst case modeling, remove servers from isolates sites in choices
        curr_ca_servers=[s for s in curr_ca_servers if s not in threshold_attack_sites[i]]
        if len(curr_ca_servers)<=server_threshold:
            threshold_attack_servers.append(curr_ca_servers)
        else:
            #servers are sorted as per above priority
            threshold_attack_servers.append(curr_ca_servers[:server_threshold])

        return threshold_attack_servers,threshold_attack_sites

    def generate_post_ca(self, initial_config,attack_servers,attack_sites):
        ca=[]
        b_servers=[]
        b_sites=[]
        for i in range(len(attack_sites)):
            curr=initial_config.copy()
            curr_sites=[]
            curr_servers=[]
            for j, site in attack_servers[i]:
                if curr[j]>0:
                    curr[j]-=1
                    curr_servers.append(site)
            for j, site in attack_sites[i]:
                curr[j]=0
                curr_sites.append(site)
            ca.append(curr)
            b_sites.append(curr_sites)
            b_servers.append(curr_servers)
        return ca,b_servers,b_sites

    def __init__(self, SITE_PROB, SERVER_PROB):
        self.curr = 0
        self.count = int(FLAGS.random_count)
        self.SITE_PROB = SITE_PROB
        self.SERVER_PROB = SERVER_PROB
        self.probability_choice = int(FLAGS.probability_choice)
        self.server_threshold = int(FLAGS.server_threshold)
        self.sites_threshold = int(FLAGS.sites_threshold)
        self.initial_config = FLAGS.configuration # for all the three reconf_strategies 'preemptive', 'post_hurricane', 'post_CA'
        self.rand_servers = []
        total_num_of_servers = sum([int(i) for i in self.initial_config.split("+")])
        for i in range(total_num_of_servers):
            # self.rand_servers.append(np.random.RandomState(3*(i+1))) # good seed for 1000
            self.rand_servers.append(np.random.RandomState(i+1))
        self.rand_sites = []
        total_num_of_sites = len(self.initial_config.split("+"))
        for i in range(total_num_of_sites):
            # self.rand_sites.append(np.random.RandomState((i+1)*100)) # good seed for 1000
            self.rand_sites.append(np.random.RandomState((i*100)))
        self.initial_config=self.initial_config.split('+')
        self.initial_config=[int(x)for x in self.initial_config]
        self.site2status = site2status_dict(self.initial_config)
        self.available_servers=[]
        for id,(k, v) in enumerate(self.site2status.items()):
            self.available_servers.extend([(id,k)]*v)
        self.random = random.Random(FLAGS.seed)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.curr < self.count:
            self.curr += 1
        
            instance_sites_choosen=[]
            instance_servers_choosen=[]
            for id,site in enumerate(self.site2status):
                rand = self.rand_sites[id].randint(1,101)
                if rand <= self.SITE_PROB:
                    instance_sites_choosen.append((id,site))
            for id,server in enumerate(self.available_servers):
                rand = self.rand_servers[id].randint(1,101)
                if rand <= self.SERVER_PROB:
                    instance_servers_choosen.append(server)

            attack_sites = [instance_sites_choosen]
            attack_servers= [instance_servers_choosen]
            
            if(self.probability_choice==1 and (self.sites_threshold or self.server_threshold)):
                #print("***********Probabilistic Method + Random choice with {} server threshold and {} site threshold".format(self.server_threshold,self.sites_threshold))
                attack_servers,attack_sites= self.attack_with_threshold_random(attack_servers,attack_sites,self.server_threshold,self.sites_threshold)
            if(self.probability_choice==2 and (self.sites_threshold or self.server_threshold)):
                #print("***********Probabilistic Method + Worst choice with {} server threshold and {} site threshold".format(self.server_threshold,self.sites_threshold))
                attack_servers,attack_sites= self.attack_with_threshold_worst(attack_servers,attack_sites,self.server_threshold,self.sites_threshold,self.initial_config,self.site2status)

            #Generate post cyber attack status
            ca,b_servers,b_sites=self.generate_post_ca(self.initial_config,attack_servers,attack_sites)

            return ca[0],b_servers[0],b_sites[0]
        else:
            raise StopIteration

class combined_table_iterator:
    ''' returns the combined instances from cyberattack_table, intrusion_table, isolation_table '''
    # turtles all the way down
    def __init__(self, post_hurricane_iterator, cyberattack_combined_iterator, reconfig_iterator, f_k_iterator): # cyberattack_combined_iterator includes instances from cyberattack_table, intrusion_table, isolation_table
        self.post_hurricane_iterator: post_hurricane_instances = post_hurricane_iterator
        self.cyberattack_combined_iterator = cyberattack_combined_iterator
        self.reconfig_iterator = reconfig_iterator
        self.f_k_iterator = f_k_iterator
        self.counter_cyberattack_combined_table = 0
        self.counter_cyberattack_combined_table_total = int(FLAGS.random_count)
        self.copy_of_cyberattack_combined_iterator = deepcopy(cyberattack_combined_iterator)
        self.copy_of_reconfig_iterator = deepcopy(reconfig_iterator)
        self.copy_of_f_k_iterator = deepcopy(f_k_iterator)
        self.this_hurricane = next(self.post_hurricane_iterator)
        self.first_time_run = True
        if FLAGS.reconfiguration == 0 and FLAGS.method in [2, 3]:
            self.config_instance_non_method1 = next(self.reconfig_iterator)
            self.f_k_instance_non_method1 = next(self.f_k_iterator)
            self.is_OOB = None
        elif FLAGS.reconfiguration == 1 and FLAGS.method in [2, 3]:
            if FLAGS.events_sequence == 2:
                self.pre_generated_attacks = []
                for _ in range(self.counter_cyberattack_combined_table_total):
                    this_cyberattack_result, intrusion_instance, isolation_instance = next(self.cyberattack_combined_iterator)
                    self.pre_generated_attacks.append([this_cyberattack_result, intrusion_instance, isolation_instance])
                self.reconfig_iterator = reconfigured_system_config_instances(context='call_from_combined_table_method_2/3', pre_generated_attacks_list = self.pre_generated_attacks)
            else:
                self.config_instance_non_method1, f_k_iterator, is_OOB = next(self.reconfig_iterator)
                self.f_k_instance_non_method1 = next(f_k_iterator)
                self.is_OOB = is_OOB

    def __iter__(self):
        return self

    def __next__(self):
        try:
            if FLAGS.method == 1:
                if self.first_time_run:
                    self.first_time_run = False
                else:
                    self.this_hurricane = next(self.post_hurricane_iterator)
                this_hurricane = self.this_hurricane
                this_cyberattack_result, intrusion_instance, isolation_instance = next(self.cyberattack_combined_iterator)
                if FLAGS.reconfiguration == 0:
                    config_instance = next(self.reconfig_iterator)
                    f_k_instance = next(self.f_k_iterator)
                    is_OOB = None
                else:
                    config_instance, f_k_iterator, is_OOB = next(self.reconfig_iterator)
                    f_k_instance = next(f_k_iterator)
                
                if FLAGS.events_sequence == 0:
                    state = []
                    for k in range(len(this_hurricane)):
                        state.append(min(this_hurricane[k], this_cyberattack_result[k]))
                elif FLAGS.events_sequence == 1:
                    state = this_cyberattack_result
                elif FLAGS.events_sequence == 2:
                    if FLAGS.reconfiguration == 0:
                        state = this_cyberattack_result
                    else:
                        # here reconfig was done but without the knowledge of intrusions. Therefore merge reconfig with cyberattack result.
                        state = self._merge_reconfig_with_CA_result_es2(config_instance, this_cyberattack_result, isolation_instance, this_hurricane)
                        
                combined_entry = [
                    this_hurricane,
                    this_cyberattack_result,
                    state,
                    intrusion_instance,
                    isolation_instance,
                    config_instance, # post-reconf
                    f_k_instance,
                    is_OOB
                ]

            elif FLAGS.method == 2 or FLAGS.method == 3:
                self.counter_cyberattack_combined_table += 1
                if self.counter_cyberattack_combined_table > self.counter_cyberattack_combined_table_total:
                    # next instance of hurricane, reset other table iterators. We are moving like this: hurricane 1 with cyberattack 1, hurricane 1 with cyberattack 2, hurricane 1 with cyberattack 3, ... hurricane 2 with cyberattack 1, hurricane 2 with cyberattack 3, hurricane 2 with cyberattack 3, ...   
                    self.this_hurricane = next(self.post_hurricane_iterator)
                    self.cyberattack_combined_iterator = deepcopy(self.copy_of_cyberattack_combined_iterator)
                    if FLAGS.reconfiguration == 0:
                        self.config_instance_non_method1 = next(self.reconfig_iterator)
                        self.f_k_instance_non_method1 = next(self.f_k_iterator)
                        is_OOB = None
                    else:
                        if not (FLAGS.events_sequence == 2 and FLAGS.reconfiguration == 1):
                            self.config_instance_non_method1, f_k_iterator, self.is_OOB = next(self.reconfig_iterator)
                            self.f_k_instance_non_method1 = next(f_k_iterator)
                        
                    self.counter_cyberattack_combined_table = 1
                
                if not (FLAGS.events_sequence == 2 and FLAGS.reconfiguration == 1):
                    this_hurricane = self.this_hurricane
                    config_instance = self.config_instance_non_method1
                    f_k_instance = self.f_k_instance_non_method1
                    is_OOB = self.is_OOB

                if FLAGS.events_sequence == 2 and FLAGS.reconfiguration == 1: # with FLAGS.events_sequence == 2 (with reconfiguration == 1), the attacks are pre-generated to keep consistent with the attack instances that the reconfiguration counter has
                    self.config_instance_non_method1, f_k_iterator, self.is_OOB = next(self.reconfig_iterator)
                    self.f_k_instance_non_method1 = next(f_k_iterator)
                    this_hurricane = self.this_hurricane
                    config_instance = self.config_instance_non_method1
                    f_k_instance = self.f_k_instance_non_method1
                    is_OOB = self.is_OOB

                    # the cyberattack:
                    idx = self.counter_cyberattack_combined_table - 1
                    this_cyberattack_result = self.pre_generated_attacks[idx][0]
                    intrusion_instance = self.pre_generated_attacks[idx][1]
                    isolation_instance = self.pre_generated_attacks[idx][2]
                        
                else: # for the other events sequences, do as before, use the next function on the iterator
                    this_cyberattack_result, intrusion_instance, isolation_instance = next(self.cyberattack_combined_iterator)

                state = []
                for k in range(len(this_hurricane)):
                    state.append(min(this_hurricane[k], this_cyberattack_result[k]))
                combined_entry = [
                    this_hurricane,
                    this_cyberattack_result,
                    state,
                    intrusion_instance,
                    isolation_instance,
                    config_instance,
                    f_k_instance,
                    is_OOB
                ]

            return combined_entry
        except StopIteration:
            raise StopIteration
    
    def _merge_reconfig_with_CA_result_es2(self, post_reconfig, this_cyberattack_result, isolations, post_hurricane):
        init_config = [int(s) for s in (FLAGS.configuration).split('+')]
        state = this_cyberattack_result
        num_sites_initially = len(init_config)
        num_sites_post_reconf = len(post_reconfig)
        num_of_CCs_isolated = len([i for i in isolations if 'CC' in i])
        num_of_DCs_isolated = len([i for i in isolations if 'DC' in i])
        # print(f'ccs isolated = {num_of_CCs_isolated}')
        # print(f'dcs isolated = {num_of_DCs_isolated}')

        # case1: no site isolations (may or may not have intrusions)
        if num_sites_post_reconf == num_sites_initially:
            # no site isolation in the CA. Since intrusions are not detectable in our model and only isolations are:
            state = this_cyberattack_result
        else:
            # case2: Only DCs isolated:
            if (num_of_DCs_isolated >= 1) and (num_of_CCs_isolated == 0):
                state = []
                for i in range(int(FLAGS.num_CCs)):
                    state.append(this_cyberattack_result[i])
            # case3: At least 1 CC isolated
            else: # a CC isolated/downed
                # up CCs are now the only sites in the system after reconf
                if isolations == []: # i.e. no CA isolations (may have hurricane-downed sites)
                    state = post_reconfig
                else:
                    isolated_CC_nums = [] # from the CA
                    for i in isolations:
                        if 'CC' in i:
                            isolated_CC_nums.append(int(i[2:]))
                    
                    all_CC_nums = [i+1 for i in range(int(FLAGS.num_CCs))]
                    # up_CC_nums = all_CC_nums - isolated_CC_nums

                    flooded_CC_nums = [f'CC{i+1}' for i in range(len(all_CC_nums))]
                    for i in range(len(post_hurricane)):
                        site = post_hurricane[i]
                        if site == 0:
                            flooded_CC_nums.append(i+1)

                    up_CC_nums = []
                    for i in all_CC_nums:
                        if i not in isolated_CC_nums and i not in flooded_CC_nums:
                            up_CC_nums.append(i)
                    
                    state = []
                    for i in range(int(FLAGS.num_CCs)):
                        if i+1 in up_CC_nums:
                            state.append(this_cyberattack_result[i])

        
        return state

def cyberattack_method(bucket_dependent_info):
    """
    Reads the bucket-dependent information that it receives as the parameter to figure out if the cyberattack type is supposed to be worst-case attack, uniformly random, or probabilistic attack and returns the correct iterator for the attack type.

    :param bucket_dependent_info: the function 'info_from_bucket_flag' returns this
    :return: returns an iterator object for the cyberattack
    """ 

    SITE_PROB, SERVER_PROB, sites, servers = bucket_dependent_info
    if FLAGS.method == 1:
        # WORST CASE
        cyberattack_iterator = worst_cyberattack_instances(sites, servers) # FLAGS.hurricane_knowledge handled inside the class

    if FLAGS.method == 2:
        # RANDOM CASE
        cyberattack_iterator = random_cyberattack_instances(sites, servers)

    if FLAGS.method == 3:
        # PROBABILISTIC CASE
        cyberattack_iterator = probabilistic_cyberattack(SITE_PROB, SERVER_PROB)

    return cyberattack_iterator