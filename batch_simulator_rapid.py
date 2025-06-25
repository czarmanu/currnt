#!/usr/bin/env python3
# *****************************************************************************
# batch_simulator_rapid.py
# *****************************************************************************

# Purpose:
# Factory function to run batch rapid simulations
# Authors:
# Manu Tom, Cedric H. David, 2023-2025

import subprocess
import logging
import os
import time

# Configure logging
log_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                             'logs_rapid_simulations.txt'))
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
# Define the start and end years
start_year = 1980
end_year = 1980
# Months to process
months = ["01", "02", "03", "04", "05", "06",
          "07", "08", "09", "10", "11", "12"]
# LSM experiments to consider
lsm_exps = ["GLDAS"]
# always 3H for rapid
lsm_stps = ["3H"]
basin_ids = ["74"]
# AWS S3 bucket name
bucket_name = "currnt-data"
# Architecture ("x86_64", "arm64")
arch = "x86_64"
# Time to wait between retries (in seconds)
retry_interval = 10


# Custom exception for token expiry
class TokenExpiredException(Exception):
    pass


# *****************************************************************************
# Check if the file exists in the specified S3 bucket
# *****************************************************************************
def check_file_exists(bucket_name, file_path):
    exists_command = (
        f"aws s3 ls s3://{bucket_name}/{file_path} "
        f"--profile saml-pub"
            )
    result = subprocess.run(exists_command, shell=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if "ExpiredToken" in result.stderr.decode():
        raise TokenExpiredException("ERROR: AWS Token expired.")
    return result.returncode == 0


# *****************************************************************************
# Process the files for the given parameters
# *****************************************************************************
def process_files(basin_id, year, month, lsm_exp, lsm_mod, lsm_stp):
    m3_file_path = (
        f"pfaf_{basin_id}/{lsm_exp}/{lsm_mod}/{lsm_stp}/{year}-{month}/"
        f"m3_riv_pfaf_{basin_id}_{lsm_exp}_{lsm_mod}_"
        f"{lsm_stp}_{year}-{month}_utc.nc4"
        )
    qout_file_path = (
        f"pfaf_{basin_id}/{lsm_exp}/{lsm_mod}/{lsm_stp}/{year}-{month}/"
        f"Qout_pfaf_{basin_id}_{lsm_exp}_{lsm_mod}_{lsm_stp}_{year}-{month}.nc"
        )
    m3_exists = check_file_exists(bucket_name, m3_file_path)
    qout_exists = check_file_exists(bucket_name, qout_file_path)
    if m3_exists and not qout_exists:
        message = (
            f"Processing files for {year}-{month}, Basin ID: {basin_id}, "
            f"LSM Experiment: {lsm_exp}, "
            f"LSM Model: {lsm_mod}, "
            f"LSM Step: {lsm_stp}"
            )
        logging.info(message)
        print(message)

        # Select API Gateway based on architecture
        if arch == "x86_64":
            api_id = "89uomm6sf8"
        elif arch == "arm64":
            api_id = "ppmkq1erca"
        else:
            raise ValueError(f"Unsupported architecture: {arch}")

        command = (
            "awscurl --region us-west-2 --service execute-api "
            "--profile saml-pub -X POST "
            f"-d '{{\"basin_id\":\"{basin_id}\", "
            f"\"lsm_exp\":\"{lsm_exp}\", "
            f"\"lsm_mod\":\"{lsm_mod}\", "
            f"\"lsm_stp\":\"{lsm_stp}\", "
            f"\"s3_name\":\"{bucket_name}\", "
            f"\"yyyy_mm\":\"{year}-{month}\"}}' "
            f"https://{api_id}.execute-api.us-west-2.amazonaws.com/"
            "dev/processes/dx1822/execution/sqs-post"
            )
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, error = process.communicate()
        if error:
            error_message = (
                f"Error processing files for {year}-{month}: "
                f"{error.decode()}"
                )
            logging.error(error_message)
            print(error_message)
        else:
            print("Output:", output.decode())
    elif not m3_exists:
        warning_message = (
            f"m3 file does not exist for {year}-{month}, "
            f"Basin ID: {basin_id}, "
            f"LSM Experiment: {lsm_exp}, "
            f"LSM Model: {lsm_mod}, "
            f"LSM Step: {lsm_stp}"
            )
        logging.warning(warning_message)
        print(warning_message)
    elif qout_exists:
        info_message = (
            f"Both m3 and Qout files exist for {year}-{month}, skipping, "
            f"Basin ID: {basin_id}, "
            f"LSM Experiment: {lsm_exp}, "
            f"LSM Model: {lsm_mod}, "
            f"LSM Step: {lsm_stp}"
            )
        logging.info(info_message)
        print(info_message)


# *****************************************************************************
# Get the LSM models based on the LSM exp
# *****************************************************************************
def get_lsm_mods(lsm_exp):
    if lsm_exp == "GLDAS":
        return ["VIC"]
    elif lsm_exp == "NLDAS":
        return ["VIC", "NOAH", "MOS"]
    else:
        return []


# *****************************************************************************
# Multi-year simulations
# *****************************************************************************
max_retry_attempts = 25  # Define a maximum number of retry attempts
try:
    for basin_id in basin_ids:
        for lsm_exp in lsm_exps:
            lsm_mods = get_lsm_mods(lsm_exp)
            for lsm_mod in lsm_mods:
                for lsm_stp in lsm_stps:
                    for year in range(start_year, end_year + 1):
                        t_start = time.time()
                        for month in months:
                            if year == 1979:
                                process_files(
                                    basin_id, year, month, lsm_exp,
                                    lsm_mod, lsm_stp
                                )
                            else:
                                qinit_file_path = (
                                    f"pfaf_{basin_id}/{lsm_exp}/{lsm_mod}/"
                                    f"{lsm_stp}/{year}-{month}/Qinit_pfaf_"
                                    f"{basin_id}_{lsm_exp}_{lsm_mod}_"
                                    f"{lsm_stp}_{year}-{month}.nc"
                                )
                                retry_count = 0  # Initialize retry count
                                while (
                                    retry_count < max_retry_attempts and
                                    not check_file_exists(
                                        bucket_name, qinit_file_path
                                    )
                                ):
                                    message = (
                                        f"Qinit file does not exist for "
                                        f"{year}-{month}, Basin ID: "
                                        f"{basin_id}. "
                                        f"Waiting and retrying."
                                    )
                                    logging.info(message)
                                    print(message)  # Print the message
                                    time.sleep(retry_interval)
                                    retry_count += 1
                                if retry_count == max_retry_attempts:
                                    error_message = (
                                        f"Max retry attempts reached for "
                                        f"{year}-{month}, Basin ID: "
                                        f"{basin_id}. Quitting."
                                    )
                                    logging.error(error_message)
                                    print(error_message)
                                    raise RuntimeError(error_message)
                                else:
                                    process_files(
                                        basin_id, year, month, lsm_exp,
                                        lsm_mod, lsm_stp
                                    )
                        t_end = time.time()
                        total_runtime = t_end - t_start
                        print(
                            f"[Profiling] Total RunTime: "
                            f"{total_runtime:.2f} seconds"
                            )
except TokenExpiredException as e:
    logging.error(str(e))
    print(str(e))


# *****************************************************************************
# End
# *****************************************************************************
