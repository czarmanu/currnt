# !/usr/bin/env python3
# *****************************************************************************
# batch_simulator_rrr.py
# *****************************************************************************

# Purpose:
# Factory function to run batch rrr simulations
# Authors:
# Manu Tom, Cedric H. David, 2023-2025

import subprocess
import logging
import time

# Define the start and end years
start_year = 1980
end_year = 1980
# Define the months to process
months = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11",
          "12"]
# Define the land surface model experiments
lsm_exps = ["GLDAS"]
# Define the basin IDs
basin_ids = ["74"]
# Define the S3 bucket name
bucket_name = "currnt-data"
# Architecture ("x86_64", "arm64")
arch = "arm64"
# Set up logging
logging.basicConfig(filename='logs_rrr_simulations.txt', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# *****************************************************************************
# Check if a file exists in S3
# *****************************************************************************
def s3_file_exists(s3_file_path):
    check_command = f"aws s3 ls {s3_file_path} --profile saml-pub"
    process = subprocess.Popen(check_command, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        error_message = f"Error checking S3: {error.decode()}"
        logging.error(error_message)
        print(error_message)
        return False
    return bool(output)


# *****************************************************************************
# Initiate the process by sending a POST request, API->SQS
# *****************************************************************************
def send_message(basin_id, lsm_exp, lsm_mod, lsm_stp, bucket_name,
                 year, month):
    # Select API Gateway based on architecture
    if arch == "x86_64":
        api_id = "qs4oqdywqc"
    elif arch == "arm64":
        api_id = "elsqd6gtu1"
    else:
        raise ValueError(f"Unsupported architecture: {arch}")

    command = (
        f"awscurl --region us-west-2 --service execute-api --profile saml-pub "
        f"--data '{{\"messageGroupId\": \"default-group\"}}' -X POST "
        f"-d '{{\"basin_id\":\"{basin_id}\", \"lsm_exp\":\"{lsm_exp}\", "
        f"\"lsm_mod\":\"{lsm_mod}\", \"lsm_stp\":\"{lsm_stp}\", "
        f"\"s3_name\":\"{bucket_name}\", \"yyyy_mm\":\"{year}-{month}\"}}' "
        f"\"https://{api_id}.execute-api.us-west-2.amazonaws.com/"
        f"dev/processes/dx1822/execution/sqs-post\""
        )
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    output, error = process.communicate()
    if error:
        error_message = f"Error initiating process: {error.decode()}"
        logging.error(error_message)
        print(error_message)
    else:
        success_message = (
            f"HTTP POST send for Basin ID: {basin_id}, "
            f"LSM Experiment: {lsm_exp}, "
            f"LSM Model: {lsm_mod}, "
            f"LSM Step: {lsm_stp}, "
            f"Year: {year}, "
            f"Month: {month}. "
            f"Response: {output.decode()}"
            )
        logging.info(success_message)
        print(success_message)


# *****************************************************************************
# Return LSM models and steps based on the LSM exp
# *****************************************************************************
def get_lsm_mods_and_stps(lsm_exp):
    if lsm_exp == "GLDAS":
        return ["VIC"], ["3H"]
    elif lsm_exp == "NLDAS":
        return ["VIC", "NOAH", "MOS"], ["H", "M"]
    else:
        return [], []


# *****************************************************************************
# Collect all combinations of parameters
# *****************************************************************************
tasks = []
for basin_id in basin_ids:
    for year in range(start_year, end_year + 1):
        for month in months:
            for lsm_exp in lsm_exps:
                lsm_mods, lsm_stps = get_lsm_mods_and_stps(lsm_exp)
                for lsm_mod in lsm_mods:
                    for lsm_stp in lsm_stps:
                        s3_file_path = (
                            f"s3://{bucket_name}/pfaf_{basin_id}/"
                            f"{lsm_exp}/{lsm_mod}/{lsm_stp}/"
                            f"{year}-{month}/m3_riv_pfaf_{basin_id}_"
                            f"{lsm_exp}_{lsm_mod}_{lsm_stp}_"
                            f"{year}-{month}_utc.nc4"
                            )
                        tasks.append((basin_id, lsm_exp, lsm_mod, lsm_stp,
                                      bucket_name, year, month, s3_file_path))


# *****************************************************************************
# Process tasks until all files exist in S3
# *****************************************************************************
while tasks:
    # Iterate over a copy of the tasks list to allow removal of tasks
    # while iterating
    for task in tasks[:]:
        (basin_id, lsm_exp, lsm_mod, lsm_stp, bucket_name, year, month,
         s3_file_path) = task

        if s3_file_exists(s3_file_path):
            message = f"File exists: {s3_file_path}"
            logging.info(message)
            print(message)
            tasks.remove(task)  # Remove the task once the file is found
        else:
            send_message(basin_id, lsm_exp, lsm_mod, lsm_stp, bucket_name,
                         year, month)
    # If there are still tasks remaining, wait for 20 minutes before retrying
    if tasks:
        time.sleep(20*60)


# *****************************************************************************
# End
# *****************************************************************************
