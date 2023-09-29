#!/usr/bin/env python

import pandas as pd
import random as rd
from collections import defaultdict

def topo_sort(sites,independent_sites,depndt_sites,prob_debs):
    neighs=defaultdict(set)
    indegree=defaultdict(int)
    
    for site,deps in prob_debs.items():
        for dep in deps:
            neighs[dep].add(site)
            indegree[site]+=1
    que=[]
    for site in sites:
        if site=="ID":
            continue
        if indegree[site]==0:
            que.append(site)
    res=[]
    while que:
        curr=que.pop()
        res.append(curr)
        for neigh in neighs[curr]:
            indegree[neigh]-=1
            if indegree[neigh]==0:
                que.append(neigh)
    res=[r for r in res if r not in independent_sites]
    return res



def generator(itr_rounds, sites, prob_debs, probs, fname):
    rd.seed(0)
    #Take dataframe with all sites
    data = pd.DataFrame(columns= sites)
    for itr_round in range(1,itr_rounds+1):
        data.at[itr_round,'ID']=itr_round

    # Extract all independent and dependent sites
    independent_sites=[]
    depndt_sites=[]
    for site,debs in prob_debs.items():
        if len(debs)==0:
            independent_sites.append(site)
        else:
            depndt_sites.append(site)
    
    #toposort dependent sites so that we have order of generation
    if len(depndt_sites)>1:
        depndt_sites=topo_sort(sites,independent_sites,depndt_sites,prob_debs)
    
    #Fill state for each independent site for all itr_rounds
    generated_sites=[]
    for site in independent_sites:
        num_of_probable_not_effected=probs[site]*itr_rounds
        # print("Independent site=",site,num_of_probable_not_effected)
        for itr_round in range(1,itr_rounds+1):
            random_number = rd.randint(1, itr_rounds)      

            site_failed=0
            if random_number > num_of_probable_not_effected: 
                site_failed = 1                       
            data.at[itr_round, site] = site_failed
        generated_sites.append(site)

    #Get dependent site (in topo order) and generate its state based on its dependent sites genrated state
    for site in depndt_sites:
        for itr_round in range(1,itr_rounds+1):
            deps_state=[]
            for dep in prob_debs[site]:
                dep_state=data.at[itr_round,dep]
                if dep_state==0:
                    deps_state.append(dep)
                else:
                    deps_state.append("not"+dep)
            deps_state="_".join(deps_state)
            num_of_probable_not_effected=probs[site][deps_state]*itr_rounds
            random_number = rd.randint(1, itr_rounds)      

            site_failed=0
            if random_number > num_of_probable_not_effected: 
                site_failed = 1                       
            data.at[itr_round, site] = site_failed
        generated_sites.append(site)

    stats_names = ["CC1","CC2","DC1","DC2","DC3","CC1andCC2","CC1orCC2","CC1andCC2andDC1","CC1orDC1","CC2orDC1"]
    stats = {key: 0 for key in stats_names}
    for itr_round in range(1, itr_rounds+1):
        cc1 = data.at[itr_round,"CC1"]
        cc2 = data.at[itr_round,"CC2"]
        dc1 = data.at[itr_round,"DC1"]
        dc2 = data.at[itr_round,"DC2"]
        dc3 = data.at[itr_round,"DC3"]

        if cc1==0:
            stats["CC1"] += 1

        if cc2==0:
            stats["CC2"] += 1

        if dc1==0:
            stats["DC1"] += 1

        if dc2==0:
            stats["DC2"] += 1

        if dc3==0:
            stats["DC3"] += 1

        if (cc1==0) and (cc2==0):
            stats["CC1andCC2"] += 1

        if(cc1+cc2<=1):
            stats["CC1orCC2"] += 1

        if (cc1==0) and (cc2==0) and (dc1==0):
            stats["CC1andCC2andDC1"] += 1

        if(cc1+dc1<=1):
            stats["CC1orDC1"] += 1

        if(cc2+dc1<=1):
            stats["CC2orDC1"] += 1



    filename = fname + str(itr_rounds)

    with open(filename+"_stats.txt", 'w') as f: 
        for key, value in stats.items():
            value = str(round(((value/itr_rounds)*100), 2)) + "%" 
            f.write('%s: %s\n' % (key, value))


    print("Generated Sites=",generated_sites)
    #Write to CSV
    # data=data.set_index('ID')
    data = data.astype(int).transpose()
    data.to_csv(filename+".csv",header=False)


def main():
    
    itr_rounds = 100000
    fname = "H11_Syn_CC1_CC2_DC1_DC2_DC3_"
    sites = ["ID", "CC1", "CC2", "DC1", "DC2", "DC3"]
    prob_debs={"CC1":[],"CC2":["CC1"],"DC1":["CC1","CC2"],"DC2":[],"DC3":[]}
    # probs={"CC1":0.905,"CC2":{"CC1":1,"notCC1":0},"DC1":{("CC1","CC2"):1,("CC1","notCC2"):1,("notCC1","CC2"):1,("notCC1","notCC2"):0},"DC2":0,"DC3":0}
    # probs={"CC1":0.905,"CC2":{"CC1":0.905,"notCC1":0.476},"DC1":{"CC1_CC2":0.905,"CC1_notCC2":0.905,"notCC1_CC2":0.905,"notCC1_notCC2":0.0455},"DC2":1,"DC3":1}
    
    # H11:
    probs={"CC1":0.905,"CC2":{"CC1":0.905,"notCC1":0.905},"DC1":{"CC1_CC2":0.905,"CC1_notCC2":0.905,"notCC1_CC2":0.905,"notCC1_notCC2":0.905},"DC2":1,"DC3":1}
    

    generator(itr_rounds, sites, prob_debs, probs, fname)

if __name__ == "__main__":
    main()
    
     