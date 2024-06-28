# Compound-Threat Analyzer 

The Compound-Threat Analyzer is a tool for analyzing the impact of *compound
threats* on fault- and intrusion-tolerant SCADA system architectures. A
compound threat occurs when a cyberattack is executed in the aftermath of or
concurrently with a natural hazard (e.g. flood, fire, earthquake) to compound
the damage caused by the natural hazard.

The Compound-Threat Analyzer takes as input a representation of a SCADA system
architecture, and a set of natural hazard realizations representing the effects
of the hazard on the system -- the natural hazard may cause one or more sites
in the system architecture to fail (e.g. because they were flooded). It then
determines the effect of a cyberattack on the post-hazard system. For
cyberattacks, the tool specifically considers *server intrusions*, where the
attacker can compromise a server and cause it to behave incorrectly, and *site
isolations*, where the attacker can isolate a site from the rest of the
network, preventing it from communicating with other system components. After
applying the cyberattack, the Analyzer determines the operational state of the
system: whether it continues to operate correctly (green state), or whether the
compound threat has succeeded in causing a temporary disruption (orange state),
complete system outage (red state), or incorrect (potentially malicious)
behavior (gray state). It reports the probability of the system experiencing
each operational state as the fraction of hazard+cyberattack realizations that
result in that state.

## Set up the conda environment as follows:

Install conda: https://conda.io/projects/conda/en/latest/user-guide/install/index.html

```
cd env_setup
conda env create -f environment.yml
conda activate compound_threat_analyzer
```


## Using the Compound-Threat Analyzer:

The analyzer starts from the ```main.py``` file. 

We have the following options to specify when running the program:

    - input_file: 
        specifies the input file
    - configuration: 
        specifies intrusion tolerant system configuration
    - f: 
        number of intrusions tolerated
    - k: 
        number of downed replicas tolerated
    - random_count: 
        specifies random cyber attack instances to generate
    - server_threshold: 
        specifies server intrusion threshold for random and probabilistic methods
    - sites_threshold: 
        specifies site isolation threshold for random and probabilistic methods
    - method: 
        attacker power to use - 1 means Worst, 2 means Random, and 3 means Probabilistic method
    - num_hurricane_instances: 
        specify number of hurricane instances
    - reconfiguration: 
        1 means On, 0 means Off
    - hurricane_knowledge: 
        decide whether cyberattack has hurricane knowledge for method 1 (worst case). 'yes' and 'no' are the valid options. Goes with 'no' by default.
    - probability_choice: 
        specifies the choice type in probability method with thresolds, 1 is random, 2 is worst case
    - bucket: 
        specifies what the attacker can take down. 1 - No attack, 2 - Server Intrusion only, 3 - Site Isolation only,  4 - Both Site Isolation and Server Instrusions
    - site_prob: 
        probability to use for site isolation cyberattack in method 3 (probabilistic method)
    - server_prob: 
        probability to use for server intrusion cyberattack in method 3 (probabilistic method)
    - simple_print: 
        decide whether to print simple output or more information
    - output_write_to_file: 
        decide whether to write output to file. 'yes' and 'no' are the valid options.
    - output_file: 
        output filename with path from the root directory of the project.
    - num_CCs:
        specify the number of Control Centres. By default, the first 2 sites in the config are assumed to be Control Centres.
    -save_run_table:
        decide whether to save the large run table or not. Useful in debugging. Valid choices: 'yes' and 'no'. 'no' by default.
    - reconf_rules:
        the file that contains the rules for reconfiguration. By default "reconf_rules.txt" file is used.
    - seed: 
        the integer to use as seed for randomization. Default seed is 0.
    - hurricane_subset:
        If you want to run on a subset of hurricanes in the input file. Valid inputs: 'all', '[start,end]'. For range, first hurricane is hurricane no. 1 not 0. Limits are inclusive.'
    - events_sequence:
        The sequence of events, specifically the reconfiguration scenarios. 0 is when reconfiguration happens based on Hurricane prediction followed by a CA. 1 is when CA is in the aftermath of hurricane and reconfiguration happends on Hurricane impact knowledge only. 2 is when CA coincide with the hurricane and reconfiguration happens with the knowledge of both.


Since each run of the analyzer is one experiment, we use scripts in the ```./experiments``` directory to run the analyzer multiple times with different parameters to generate the required results which are used by the graph generation notebooks in the same directory. As an example, see the following section "Recreating SRDS results". 

## Recreating SRDS results:
This section describes the steps to recreate the core results from our SRDS project. Note that the python scripts contain the relevant shebang in them. If you are unable to run them, try ```chmod +x script.py``` or ```python script.py```.
1. First, activate the conda environment ```conda activate compound_threat_analyzer```. See the section "Set up the conda environment as follows:" for instructions to set the environment up for the first time. 
2. Next, you need to generate the data files that the analyzer can run on. For this, starting from the this root directory of the project, change directory to ./data/hawaii_data and run the script "data_compiler.py" to generate data files for Hawaii. Next change directory to ../florida_data and run the script "data_compiler_superhurricane.py" to generate the data file for Florida.:


```
cd ./data/hawaii_data
./data_compiler.py
cd ../florida_data
./data_compiler_superhurricane.py
```

3. Next, change directory to `../../experiments` and run the script "SRDS-experiments.py" i.e. do:

```
cd ../../experiments; ./SRDS-experiments.py
```

4. Following this, run all the cells in the ```SRDS-graphs.ipynb``` notebook to generate the graphs.

Note: Experiments using the uniformly random cyberattack model (`method=2`)
take a long time to run. To run only a subset of the experiments that excludes
those using the uniformly random cyberattack model (and should finish quickly),
you can use `SRDS-experiments-subset.py` and `SRDS-graphs-subset.ipynb`
instead.

## Data files:
We have three sets of data:
1. **Hurricane impact simulation data for Hawaii:**
    The hurricane impact simulation dataset is pre-generated and saved as an .xlsx file in ```./data/hawaii_data``` directory as ```Hawaii-hurricane-data.xlsx```. This file is used to extract smaller .csv files in the format needed for the analyzer to run on. The .csv files are generated using the script ```data_compiler.py``` in the same directory. Therefore, to work with the Hawaii data, generate the data files as follows: ``` cd data/hawaii_data; python data_compiler.py ```

2. **Hurricane impact data in Florida based on a 100 year mean recurrence interval:**
    The directory ```./data/florida_data``` contains this data. In this directory, we have the file ```Florida-hurricane-data.xlsx``` that contains the site failure instances for all the sites. Similar to the case with Hawaii data, there is a script in the directory ```data_compiler_superhurricane.py``` that generates .csv files in the same fashion as with the Hawaii dataset such that the analyzer can run on these .csv files. The sites selected for the .csv files can be chosen at the start of the script. This script assumes that there is a "superhurricane" that takes down the sites in the dataset. Note that unlike Hawaii's data, this is not a simulation of an specific hurricane.

    There is another script in this directory called ```summaries-grid-maker.py``` for analysis purposes. It generates the information on when the sites go down and the correlations between the site failures in the case of the superhurricane.

3. **Synthetic hurricane data:**
    The directory ```./data/synthetic_data``` contains the script ```synthetic_hurricane_impact_generator.py``` that can be used to create synthetic hurricane data that the analyzer can use. The script can generate data based on the probabilities of each site's failure and correlated failure probabilities. The probabilities can be set in the ```main()``` function in the script by editing the dictionary objected named ```probs```. The synthetic hurricanes are not used by the SRDS experiments script, however, it can be useful for exploring the impact of correlated failures between sites in more detail.

We also have the following dummy data file:
- **No Hurricane file:**
    In the ```./data``` there is a data file name ```noHurricane_site1_site2_site3_site4_site5.csv``` which is a dummy data file in which none of the sites fails. This data file can be used with the analyzer to analyze a scenario where there is no hurricane and only cyberattacks take place. 

## Credits:

The Compound-Threat Analyzer is currently developed by the University of
Pittsburgh [Resilient Systems and Societies Lab](https://rsslab.io/) and the
Johns Hopkins University [Distributed Systems and Networks
Lab](http://www.dsn.jhu.edu).

The creators of the Compound-Threat Analyzer are: Yair Amir, Amy Babay, Sahiti
Bommareddy, Maher Khan, and Huzaifah Nadeem. Benjamin Gilby is a major
contributor, for his contributions to the initial tool design and
proof-of-concept.

Partial funding for the Compound-Threat Analyzer was provided by the  U.S.
Department of Defense (DoD), through the Strategic Environmental Research and
Development Program (SERDP) grant RC20-1138 and Installation Technology
Transition Program (ITTP) project “Severe Impact Resilience”. The
Compound-Threat Analyzer is not necessarily endorsed by the DoD.
