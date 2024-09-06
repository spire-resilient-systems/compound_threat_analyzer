#!/usr/bin/env python

import subprocess
import os
import multiprocessing

# assuming that this script runs from inside 'experiments' directory

OUTPUT_DIRECTORY = "SRDS-results" # using as: experiments/{OUTPUT_DIRECTORY}

INPUT_FILES = { # key = shorter/more descriptive name used for output file. value = path to data file
    "HI_H5Cat2_Honolulu_Waiau_DRFortress": "data/hawaii_data/H5_Cat2_honolulu_waiau_DRFotress_AlohaNap_MTP.csv",
    "FL_superhurricane_PalmBeach_PortOrange_Jacksonville": "data/florida_data/FL_superhurricane_PalmBeach_PortOrange_Jacksonville_Jacksonville_Jacksonville.csv",
    "HI_H5Cat2_Honolulu_Kahe_DRFortress": "data/hawaii_data/H5_Cat2_honolulu_kahe_DRFotress_AlohaNap_MTP.csv",
    "FL_superhurricane_PalmBeach_PortOrange_MiamiMi1": "data/florida_data/FL_superhurricane_PalmBeach_PortOrange_MiamiMI1_MiamiMI1_MiamiMI1.csv",
    "HI_H5Cat3_Honolulu_Waiau_DRFortress": 'data/hawaii_data/H5_Cat3_honolulu_waiau_DRFotress_AlohaNap_MTP.csv'
}

CONFIG_VALS = {
    '2': {
        "f": 0, 
        "k": 0
    }, 
    '2+2': {
        "f": 0, 
        "k": 0
    },
    '6': {
        "f": 1, 
        "k": 1
    },
    '6+6': {
        "f": 1, 
        "k": 1
    },
    '6+6+6': {
        "f": 1, 
        "k": 7
    },
    'r6+6+6': {
        "f": 1, 
        "k": 7
    },
}

COMMON_FLAGS = [
    "python",
    "main.py",
    "--simple_print=no",
    "--output_write_to_file=yes",
]

FIG_WISE_PARAMS = {
    '7a': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=1"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress'],
        },

    '7b': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=2"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress'],
    },

    '7c': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=3"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress'],
    },

    '7d': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=4"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress'],
    },

    '8a': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=1"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville'],
    },

    '8b': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=2"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville'],
    },

    '8c': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=3"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville'],
    },

    '8d': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=4"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville'],
    },

    # '9a': {
    #     'params': ["--method=2", "--random_count=100000", "--num_hurricane_instances=1000", "--server_threshold=1", "--sites_threshold=1", "--bucket=4"],
    #     'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
    #     'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress'],
    # },

    # '9b': {
    #     'params': ["--method=2", "--random_count=100000", "--num_hurricane_instances=1000",  "--server_threshold=1", "--sites_threshold=1", "--bucket=4"],
    #     'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
    #     'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville'],
    # },

    '10a': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=2"],
        'configs': ['6+6', '6+6+6'],
        'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress', 'HI_H5Cat2_Honolulu_Kahe_DRFortress'],
    },

    '10b': {
        'params': ["--method=2", "--random_count=100000", "--num_hurricane_instances=1000",  "--server_threshold=1", "--sites_threshold=1", "--bucket=4"],
        'configs': ['6+6', '6+6+6'],
        'sites': ['HI_H5Cat2_Honolulu_Waiau_DRFortress', 'HI_H5Cat2_Honolulu_Kahe_DRFortress'],
    },

    '11a': {
        'params': ["--num_hurricane_instances=1000", "--bucket=1"],
        'configs': ['2+2', '6+6', '6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville', 'FL_superhurricane_PalmBeach_PortOrange_MiamiMi1'],
    },

    '11b': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=4"],
        'configs': ['2+2', '6+6', '6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville', 'FL_superhurricane_PalmBeach_PortOrange_MiamiMi1'],
    },

    '11c': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=4"],
        'configs': ['1r6+6+6'],
        'sites': ['FL_superhurricane_PalmBeach_PortOrange_MiamiMi1'],
    },

    # '12a': {
    #     'params': ["--method=2", "--random_count=100000", "--num_hurricane_instances=1000",  "--server_threshold=1", "--sites_threshold=1", "--bucket=4"],
    #     'configs': ['6+6', '6+6+6', '1r6+6+6', '2r6+6+6'],
    #     'sites': ['HI_H5Cat2_Honolulu_Kahe_DRFortress'],
    # },

    # '12b': {
    #     'params': ["--method=2", "--random_count=100000", "--num_hurricane_instances=1000",  "--server_threshold=1", "--sites_threshold=1", "--bucket=4"],
    #     'configs': ['6+6', '6+6+6', '1r6+6+6', '2r6+6+6'],
    #     'sites': ['FL_superhurricane_PalmBeach_PortOrange_Jacksonville'],
    # },

    'A1a': {
        'params': ["--num_hurricane_instances=1000", "--bucket=1"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['HI_H5Cat3_Honolulu_Waiau_DRFortress'],
    },

    'A1b': {
        'params': ["--method=1", "--hurricane_knowledge=yes", "--num_hurricane_instances=1000", "--bucket=4"],
        'configs': ['2', '2+2', '6', '6+6', '6+6+6'],
        'sites': ['HI_H5Cat3_Honolulu_Waiau_DRFortress'],
    },
}

def run_command(cmd, exp_name):
    print(f'\nSTARTING EXP < {exp_name} > AS: " {cmd} " ... ')
    try:
        cmd = "cd ..; " + cmd
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"< {exp_name} > process returned")
        print(result.stdout)
        print(result.stderr)
    except SystemExit:
        pass

def main():
    cmds = []
    if not os.path.exists(f"./{OUTPUT_DIRECTORY}/"):
        os.makedirs(f"./{OUTPUT_DIRECTORY}/")
    # delete existing files in the directory, if any:
    existing_files = os.listdir(f"./{OUTPUT_DIRECTORY}/")
    for f in existing_files:
        os.remove(f"./{OUTPUT_DIRECTORY}/{f}")

    for fig in FIG_WISE_PARAMS.keys():
        counter = 1
        for sites in FIG_WISE_PARAMS[fig]['sites']:
            for conf in FIG_WISE_PARAMS[fig]['configs']:
                this_cmd = ''
                
                for p in COMMON_FLAGS:
                    this_cmd += p + ' '
                for p in FIG_WISE_PARAMS[fig]['params']:
                    this_cmd += p + ' '

                conf_param = ''
                if conf not in ['1r6+6+6', '2r6+6+6']:
                    conf_param = '--configuration=' + conf
                elif conf == '1r6+6+6':
                    conf_param = '--configuration=6+6+6' + ' --reconfiguration=1 --events_sequence=1'
                elif conf == '2r6+6+6':
                    conf_param = '--configuration=6+6+6' + ' --reconfiguration=1 --events_sequence=2'
                this_cmd += conf_param + ' '

                if conf not in ['1r6+6+6', '2r6+6+6']:
                    k_param = "--k=" + str(CONFIG_VALS[conf]["k"])
                    f_param = "--f=" + str(CONFIG_VALS[conf]["f"])
                else:
                    k_param = "--k=" + str(CONFIG_VALS['6+6+6']["k"])
                    f_param = "--f=" + str(CONFIG_VALS['6+6+6']["f"])
                this_cmd += k_param + ' ' + f_param + ' '

                input_param = "--input_file=" + INPUT_FILES[sites]
                this_cmd += input_param + ' '

                output_param = "--output_file=experiments/" + OUTPUT_DIRECTORY + "/"
                if fig not in ['10a', '10b', '10c', '11a', '11b']:
                    output_param += fig + '_' + conf + '.csv'
                    
                # elif fig in ['10a', '10b', '10c']:
                elif fig in ['10a', '10b']:
                    site_letter = 'W' if sites == 'HI_H5Cat2_Honolulu_Waiau_DRFortress' else 'K'
                    output_param += fig + '_' + conf + '_' + site_letter + '.csv'
                    
                elif fig in ['11a', '11b']:
                    site_letter = 'J' if sites == 'FL_superhurricane_PalmBeach_PortOrange_Jacksonville' else 'M'
                    output_param += fig + '_' + conf + '_' + site_letter + '.csv'
    
                this_cmd += output_param + ' '
                
                cmds.append([f"{fig}, exp {counter}", this_cmd])
                counter += 1
    
    procs = []
    for c in cmds:
        this_exp_name = c[0]
        this_cmd = c[1]
        this_proc = multiprocessing.Process(target=run_command, args=[this_cmd, this_exp_name], name=this_exp_name)
        procs.append(this_proc)
    for p in procs:
        p.start()
    for p in procs:
        p.join()

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()