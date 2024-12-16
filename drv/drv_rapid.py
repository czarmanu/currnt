#!/usr/bin/env python3
# *****************************************************************************
# drv_rapid.py
# *****************************************************************************

# Purpose:
# Python driver for running RAPID on AWS using Lambda service
# Authors:
# Manu Tom, Cedric H. David, 2023-2024


# *****************************************************************************
# Import libraries
# *****************************************************************************
import os
import subprocess
import boto3
import logging

# Following libs needed only for the one time job of 1980-01 Qinit creation
import shutil
import netCDF4 as nc
import numpy as np


# *****************************************************************************
# Driver for uploading from /tmp to s3 bucket
# *****************************************************************************
def drv_upl_S3(s3_bucket_name, f_upld, subfolder, basin_id, lsm_exp, lsm_mod,
               lsm_stp, yyyy_mm):
    s3_res = boto3.resource('s3')
    file_type = f_upld.split('/')[-1].split('_')[0]
    try:
        # Construct the desired filename for upload
        qout_filename = file_type+"_pfaf_{}_{}_{}_{}_{}.nc".format(basin_id,
                                                                   lsm_exp,
                                                                   lsm_mod,
                                                                   lsm_stp,
                                                                   yyyy_mm)

        # Upload to S3 bucket with the specified subfolder
        s3_key = "{}/{}".format(subfolder, qout_filename)
        s3_res.Bucket(s3_bucket_name).upload_file(f_upld, s3_key)

        print("File uploaded to S3:", s3_key)

    except Exception as e:
        print(f"Error uploading file to S3: {e}")


# *****************************************************************************
# Suppress debug logging for boto3 and related components
# *****************************************************************************
def suppress_debug_logging():
    loggers_to_suppress = [
        'boto3', 'botocore', 's3transfer', 'urllib3', 'botocore.endpoint',
        'botocore.loaders', 'botocore.client', 'botocore.utils',
        'botocore.hooks',
        'botocore.auth', 'botocore.retryhandler', 'botocore.session',
        'botocore.vendored.requests.packages.urllib3'
    ]
    for logger_name in loggers_to_suppress:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


# *****************************************************************************
# Driver for downloading from s3 bucket to /tmp
# *****************************************************************************
def drv_dwn_S3(s3_bucket_name, basin_id, lsm_exp, lsm_mod, lsm_stp, yyyy_mm,
               file_type):
    s3_res = boto3.resource('s3')

    # Suppress debug logging for boto3 and related components
    suppress_debug_logging()

    try:
        # Construct the S3 key with subfolders based on file_type
        if file_type == 'm3':
            s3_key = (
                "pfaf_{}/{}/{}/{}/{}/".format(
                    basin_id, lsm_exp, lsm_mod, lsm_stp, yyyy_mm
                    ) + "m3_riv_pfaf_{}_{}_{}_{}_{}_utc.nc4".format(
                    basin_id, lsm_exp, lsm_mod, lsm_stp, yyyy_mm
                )
            )

            # Create the local file path in /tmp directory
            file_local = os.path.join('/tmp',
                                      "m3_riv_pfaf_{}_{}_{}_{}_{}_utc.nc4"
                                      .format(basin_id, lsm_exp, lsm_mod,
                                              lsm_stp, yyyy_mm))

        elif file_type == 'Qinit':
            s3_key = "pfaf_{}/{}/{}/{}/{}/Qinit_pfaf_{}_{}_{}_{}_{}.nc".format(
                basin_id, lsm_exp, lsm_mod, lsm_stp, yyyy_mm,
                basin_id, lsm_exp, lsm_mod, lsm_stp, yyyy_mm)

            # Create the local file path in /tmp directory
            file_local = os.path.join(
                '/tmp',
                "Qinit_pfaf_{}_{}_{}_{}_{}_utc.nc".format(
                    basin_id, lsm_exp, lsm_mod, lsm_stp, yyyy_mm
                    )
                )

        else:
            raise ValueError("Invalid file_type. Use 'm3' or 'Qinit'.")

        # Download file from S3 bucket
        s3_res.Bucket(s3_bucket_name).download_file(s3_key, file_local)
        print("File downloaded from S3:", s3_key)

        # Check downloaded file
        result_chk_dwnld = subprocess.run(["ls", "-lR", "/tmp"],
                                          capture_output=True, text=True)
        print("Checking download folder contents:\n", result_chk_dwnld.stdout)

        # Return the subfolder for later use
        return "/".join(s3_key.split("/")[:-1])

    except Exception as e:
        print(f"An error occurred while downloading the file: {e}")
        return None  # Return None if an error occurs


# *****************************************************************************
# Driver for generating initial Qinits (Qout populated with zeros)
# *****************************************************************************
def drv_generate_initial_Qinit(qfinal_path, qinit_zeros_file_path):
    """
    Set all Qout values to zero in the specified NetCDF file while preserving
    the original precision and data type,
    and save the modified data to a new NetCDF file.

    Parameters:
    qfinal_path (str): Path to the original NetCDF file.
    qinit_zeros_file_path (str): Path to the new NetCDF file to be created.
    """
    # Copy the original file to the new file
    shutil.copyfile(qfinal_path, qinit_zeros_file_path)

    # Open the new NetCDF file in read-write mode
    with nc.Dataset(qinit_zeros_file_path, 'r+') as ds:
        # Print original Qout values for verification
        print("Original Qout values (first 10 values):")
        print(ds.variables['Qout'][:, :10])

        # Get the data type of the Qout variable
        qout_dtype = ds.variables['Qout'].dtype

        # Set all Qout values to zero while preserving
        # the original data type and precision
        ds.variables['Qout'][:] = np.zeros_like(ds.variables['Qout'][:],
                                                dtype=qout_dtype)

        # Print modified Qout values for verification
        print("Modified Qout values (first 10 values):")
        print(ds.variables['Qout'][:, :10])


# *****************************************************************************
# Driver for deleting a file
# *****************************************************************************
def drv_del_file(file_path):
    try:
        os.remove(file_path)
        print(f"File {file_path} has been deleted successfully.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except PermissionError:
        print(f"Permission denied: unable to delete {file_path}.")
    except Exception as e:
        print(f"Error occurred while deleting file {file_path}: {e}")


# *****************************************************************************
# End
# *****************************************************************************
