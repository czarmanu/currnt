# *****************************************************************************
# lambda_function_rrr.py
# *****************************************************************************

# Purpose:
# run RRR:
# 1) for 1 basin, 1 month at a time
# 2) using a python driver
# 3) using earthaccess library for Earthdata (LDAS) download
# 4) to generate the monthly LDAS file and upload it to s3 bucket
# 4) to generate the m3 file and upload it to s3 bucket
# Authors:
# Manu Tom, Cedric H. David, 2018-2024


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

# *****************************************************************************
# import libraries
# *****************************************************************************

import os
import shutil
import json
import rrr_drv_MERIT_Hydro_v07_Basins_v01_GLDAS_v20 as rrr_drv
import drv_rrr as rrr_io_drv

# *****************************************************************************
# set parameters
# *****************************************************************************
otpt_fldr = "/tmp/"


# *****************************************************************************
# lambda_handler
# *****************************************************************************
def lambda_handler(event, context):
    print(event)
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

            inpt_fldr = "/rrr/input/pfaf_" + basin_id

            ldas_fldr = "/tmp/input/pfaf_" + basin_id + "/GLDAS20/" \
                + lsm_mod + "/" + lsm_stp + "/" + yyyy_mm

            # *****************************************************************
            # create rrr object
            # *****************************************************************
            rrr = rrr_drv.RRR(basin_id, lsm_mod, lsm_stp, yyyy_mm)

            # *****************************************************************
            # driver: download
            # *****************************************************************
            rrr_drv.drv_dwn(rrr)
            print("Download driver: done")

            # *****************************************************************
            # driver: lsm
            # *****************************************************************
            rrr_drv.drv_lsm(rrr)
            print("LSM driver: done")

            # *****************************************************************
            # driver: volume
            # *****************************************************************
            con_csv = os.path.join(inpt_fldr, "rapid_connect_pfaf_" + basin_id
                                   + ".csv")
            crd_csv = os.path.join(inpt_fldr, "coords_pfaf_" + basin_id
                                   + ".csv")
            cpl_csv = os.path.join(inpt_fldr, "rapid_coupling_pfaf_" + basin_id
                                   + "_" + lsm_exp + ".csv")

            print("Copying connect, coord, coupling files from Zenodo to /tmp")
            shutil.copy(con_csv, otpt_fldr)
            shutil.copy(crd_csv, otpt_fldr)
            shutil.copy(cpl_csv, otpt_fldr)

            rrr_drv.drv_vol(rrr)
            print("Volume driver: done")

            # *****************************************************************
            # Define file paths and upload to S3 bucket
            # *****************************************************************
            m3_file = (
                f"/tmp/m3_riv_pfaf_{basin_id}_{lsm_exp}_{lsm_mod}_"
                f"{lsm_stp}_{yyyy_mm}_utc.nc4"
                )

            ldas_file = f'/tmp/{lsm_exp}_{lsm_mod}_{lsm_stp}_{yyyy_mm}_utc.nc4'

            files_to_upload = [(m3_file, 'm3'), (ldas_file, 'LDAS')]

            # Upload m3_file and ldas_file
            for file_path, label in files_to_upload:
                if os.path.exists(file_path):
                    print(f"Attempting to upload {label} file: {file_path}")
                    if rrr_io_drv.drv_upl_S3(s3_name, file_path, basin_id,
                                             lsm_exp, lsm_mod, lsm_stp,
                                             yyyy_mm):
                        print(f"{label} file uploaded successfully.")
                        rrr_io_drv.drv_del_file(file_path)
                    else:
                        print(f"Failed to upload {label} file; skipping \
                              deletion.")
                else:
                    print(f"{label} file not found at {file_path}, skipping \
                          upload.")

            # Upload all individual files in the ldas_fldr to the S3 bucket
            if os.path.exists(ldas_fldr):
                for root, dirs, files in os.walk(ldas_fldr):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        if rrr_io_drv.drv_upl_S3(s3_name, file_path, basin_id,
                                                 lsm_exp, lsm_mod, lsm_stp,
                                                 yyyy_mm):
                            rrr_io_drv.drv_del_file(file_path)
                        else:
                            print(f"Failed to upload file {filename} from \
                                  ldas folder; skipping deletion.")

                # Delete the local ldas folder after all uploads are attempted
                rrr_io_drv.drv_del_folder(ldas_fldr)
                print(f"All contents of {ldas_fldr} have been deleted \
                      successfully.")
            else:
                print(f"ldas folder not found at {ldas_fldr}, \
                      skipping upload.")

    return {'status': 'Success', 'message': message}


# *****************************************************************************
# End
# *****************************************************************************
