#!/usr/bin/env python3
# *****************************************************************************
# drv_rrr.py
# *****************************************************************************

# Purpose:
# Python driver for rrr
# Authors:
# Manu Tom, Cedric H. David, 2018-2024


# *****************************************************************************
# Import libraries
# *****************************************************************************
import boto3
import os
import shutil


# *****************************************************************************
# Driver for deleting a folder and its contents
# *****************************************************************************
def drv_del_folder(folder_path):
    """
    Deletes all contents of the specified folder, including files and
    subdirectories.

    Parameters:
    folder_path (str): Path to the folder whose contents are to be deleted.
    """
    try:
        # Check if the folder exists
        if os.path.exists(folder_path):
            # Iterate over all the files and subdirectories in the folder
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)  # Remove the file or link
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove the directory
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            print(f"All contents of {folder_path} have been deleted\
                  successfully.")
        else:
            print(f"The folder {folder_path} does not exist.")
    except Exception as e:
        print(f"Error occurred while deleting contents of folder\
              {folder_path}: {e}")


# *****************************************************************************
# Driver for uploading from /tmp to s3 bucket
# *****************************************************************************
def drv_upl_S3(s3_bucket_name, f_upld, basin_id, lsm_exp, lsm_mod, lsm_stp,
               yyyy_mm):
    s3_res = boto3.resource('s3')
    s3_client = boto3.client('s3')

    try:
        # Extract filename from file path
        fn_upld = os.path.basename(f_upld)

        # Define the S3 key with subfolders
        s3_key = "pfaf_{}/{}/{}/{}/{}/{}".format(basin_id, lsm_exp, lsm_mod,
                                                 lsm_stp, yyyy_mm, fn_upld)

        # Upload the file to S3 bucket
        s3_res.Bucket(s3_bucket_name).upload_file(f_upld, s3_key)
        print("File uploaded to S3:", s3_key)

        # Verify file size
        local_file_size = os.path.getsize(f_upld)
        s3_file_size = get_s3_file_size(s3_client, s3_bucket_name, s3_key)

        if local_file_size == s3_file_size:
            print("File sizes match, upload successful.")
            return True
        else:
            print(f"File size mismatch: local file size = {local_file_size}\
                  bytes, S3 file size = {s3_file_size} bytes")
            return False

    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return False


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
# Helper function to get S3 file size
# *****************************************************************************
def get_s3_file_size(s3_client, bucket_name, key):
    try:
        response = s3_client.head_object(Bucket=bucket_name, Key=key)
        return response['ContentLength']
    except Exception as e:
        print(f"Error getting S3 file size: {e}")
        return -1


# *****************************************************************************
# End
# *****************************************************************************
