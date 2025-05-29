# *****************************************************************************
# lambda_function_rapid.py
# *****************************************************************************

# Purpose:
# run RAPID on AWS with lambda service:
# 1) using an executable
# 2) for 1 basin, 1 month
# Authors:
# Manu Tom, Cedric H. David, 2023-2024


# *****************************************************************************
# Example invocation
# *****************************************************************************
# {
#     "basin_id": "74",
#     "lsm_exp": "GLDAS",
#     "lsm_mod": "VIC"
#     "lsm_stp": "3H"
#     "yyyy_mm": "2000-01"
#     "s3_name": "currnt-data"
# }

import subprocess
import os
import shutil
import json
import time
import resource
import drv_rapid as rapid_io_drv
import drv_MERIT_Hydro_v07_Basins_v01_GLDAS_v20 as rapid_drv


# *****************************************************************************
# lambda_handler
# *****************************************************************************
def lambda_handler(event, context):
    ns_runtime = 0.0
    t_start = time.time()
    rapid_io_drv.suppress_debug_logging()  # Suppress debug messages
    print("received event: ", event)
    for record in event['Records']:
        sqs_body = record['body']
        # Split the body content into individual JSON objects
        messages = sqs_body.strip().split('\n')

        # Process each message separately
        for message in messages:
            message_data = json.loads(message)
            basin_id = message_data.get('basin_id')
            lsm_exp = message_data.get('lsm_exp')
            lsm_mod = message_data.get('lsm_mod')
            lsm_stp = message_data.get('lsm_stp')
            yyyy_mm = message_data.get('yyyy_mm')
            s3_name = message_data.get('s3_name')

            # Print extracted data for debugging
            print("basin_id:", basin_id)
            print("lsm_mod:", lsm_mod)
            print("lsm_stp:", lsm_stp)
            print("yyyy_mm:", yyyy_mm)
            print("s3_name:", s3_name)

            # *****************************************************************
            # Download m3 and Qinit files from s3 to /tmp
            # *****************************************************************
            subfolder = rapid_io_drv.drv_dwn_S3(s3_name, basin_id, lsm_exp,
                                                lsm_mod, lsm_stp, yyyy_mm,
                                                'm3')

            # If subfolder is None, skip the rest of the processing
            if subfolder is None:
                continue

            # for all months except 1979-12
            # Note: 1979-12 only used to create Qinit of 1980-01 with zeros
            if (yyyy_mm != "1979-12"):
                subfolder = rapid_io_drv.drv_dwn_S3(s3_name, basin_id, lsm_exp,
                                                    lsm_mod, lsm_stp, yyyy_mm,
                                                    'Qinit')

            # If subfolder is None, skip the rest of the processing
            if subfolder is None:
                continue

            m3_file = os.path.join('/tmp',
                                   "m3_riv_pfaf_{}_{}_{}_{}_{}_utc.nc4".format(
                                       basin_id, lsm_exp, lsm_mod, lsm_stp,
                                       yyyy_mm))

            q_init_file = '/tmp/Qinit_pfaf_' + basin_id + '_' + lsm_exp + '_' \
                + lsm_mod + '_' + lsm_stp + '_' + yyyy_mm + '_utc.nc'

            # *****************************************************************
            # Check inputs downloaded from zenodo
            # *****************************************************************
            input_files_check = subprocess.run(["ls", "-lR",
                                                '/rapid/input/pfaf_'
                                                + basin_id + '/'],
                                               capture_output=True, text=True)

            print("Contents (/rapid/input/pfaf_XX):\n",
                  input_files_check.stdout)

            # *****************************************************************
            # Run RAPID and check Qout in /tmp
            # *****************************************************************
            rapid = rapid_drv.RAPID(basin_id, lsm_mod, lsm_stp, yyyy_mm)

            # Write the namelist file
            rapid_drv.drv_write_namelist(rapid)

            namelist_file = os.path.join('/tmp',
                                         "rapid_namelist_pfaf_{}_{}_{}_{}_{}".
                                         format(basin_id, lsm_exp, lsm_mod,
                                                lsm_stp, yyyy_mm))

            # Run RAPID
            t_ns_start = time.time()
            rapid_drv.drv_run(rapid)
            t_ns_end = time.time()
            ns_runtime = t_ns_end - t_ns_start
            result_filegen_check = subprocess.run(["ls", "-lR", '/tmp'],
                                                  capture_output=True,
                                                  text=True)
            print("Contents (/tmp):\n", result_filegen_check.stdout)

            # *****************************************************************
            # Upload Qout and Qfinal (as Qinit of next month) files from /tmp
            # to the S3 bucket
            # *****************************************************************
            q_out_file = '/tmp/Qout_pfaf_' + basin_id + '_' + lsm_exp + '_' + \
                lsm_mod + '_' + lsm_stp + '_' + yyyy_mm + '_utc.nc'

            rapid_io_drv.drv_upl_S3(s3_name, q_out_file, subfolder, basin_id,
                                    lsm_exp, lsm_mod, lsm_stp, yyyy_mm)

            q_final_file = '/tmp/Qfinal_pfaf_' + basin_id + '_'\
                + lsm_exp + '_' + lsm_mod + '_' + lsm_stp + '_'\
                + yyyy_mm + '_utc.nc'

            # upload Qfinal of current month as Qinit of next month
            if yyyy_mm.endswith('12'):  # for December to January transition
                next_month = str(int(yyyy_mm[:4]) + 1) + '-01'
            else:
                next_month = yyyy_mm[:5] + str(int(yyyy_mm[5:]) + 1).zfill(2)

            subfolder = subfolder.replace(yyyy_mm, next_month)
            q_init_file_nxt_month = '/tmp/Qinit_pfaf_' + basin_id + '_'\
                + lsm_exp + '_' + lsm_mod + '_' + lsm_stp + '_'\
                + next_month + '_utc.nc'

            shutil.copyfile(q_final_file, q_init_file_nxt_month)
            rapid_io_drv.drv_upl_S3(s3_name, q_init_file_nxt_month, subfolder,
                                    basin_id, lsm_exp, lsm_mod, lsm_stp,
                                    next_month)

            print("Upload driver: done")

            # only for 1979-12
            # generate the Qinit file (with Qout as zeros) for 1980-01
            # from the Qfinal of 1979-12
            if (yyyy_mm == "1979-12"):
                q_init_zeros_file = '/tmp/Qinit_pfaf_' + basin_id + '_'\
                    + lsm_exp + '_' + lsm_mod + '_' + lsm_stp + '_'\
                    + next_month + '_utc.nc'

                rapid_io_drv.drv_generate_initial_Qinit(q_final_file,
                                                        q_init_zeros_file)
                rapid_io_drv.drv_upl_S3(s3_name, q_init_zeros_file, subfolder,
                                        basin_id, lsm_exp, lsm_mod, lsm_stp,
                                        next_month)

            # *****************************************************************
            # Delete Qout, Qfinal, m3, Qinit, namelist files from /tmp
            # *****************************************************************
            if (yyyy_mm != "1979-12"):  # no Qinit for 1979-12
                rapid_io_drv.drv_del_file(q_init_file)
            rapid_io_drv.drv_del_file(m3_file)
            rapid_io_drv.drv_del_file(q_out_file)
            rapid_io_drv.drv_del_file(q_final_file)
            rapid_io_drv.drv_del_file(q_init_file_nxt_month)
            rapid_io_drv.drv_del_file(namelist_file)

            # only for 1979-12
            if (yyyy_mm == "1979-12"):
                rapid_io_drv.drv_del_file(q_init_zeros_file)

            result_filegen_check = subprocess.run(["ls", "-lR", '/tmp'],
                                                  capture_output=True,
                                                  text=True)
            print("Contents (/tmp):\n", result_filegen_check.stdout)

            message = ' {} using m3 input from s3 bucket\
                {} and uploaded Qout to s3 bucket {}!'.format(
                basin_id, s3_name, s3_name)
    t_end = time.time()
    total_runtime = t_end - t_start
    max_mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(f"[Profiling] Total RunTime: {total_runtime:.2f} seconds")
    print(f"[Profiling] Numerical Simulation Time: {ns_runtime:.2f} seconds")
    print(f"[Profiling] Max Memory Usage: {max_mem_mb:.2f} MB")
    return {
        'status': 'Success',
        'profiling': {
            'runtime_total_sec': total_runtime,
            'runtime_ns_sec': ns_runtime,
            'memory_max_MB': max_mem_mb
            }
        }

# *****************************************************************************
# End
# *****************************************************************************
