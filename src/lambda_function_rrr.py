# *****************************************************************************
# lambda_function_rrr.py
# *****************************************************************************

# Purpose:
# run RRR on AWS cloud using Lambda service:
# 1) for 1 basin, 1 month at a time
# 2) using a python driver
# 3) using earthaccess library for Earthdata (LDAS) download
# 4) to generate the monthly LDAS file and upload it to s3 bucket
# 4) to generate the m3 file and upload it to s3 bucket
# Authors:
# Manu Tom, Cedric H. David, 2023-2025


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
import boto3
import time
import resource
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
    t_start = time.time()
    ed_dwnld_runtime = 0.0
    zen_runtime = 0.0
    lsm_runtime = 0.0
    vol_runtime = 0.0
    s3_dwnld_runtime = 0.0
    s3_upld1_runtime = 0.0
    s3_upld2_runtime = 0.0
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
            ldas_file_key = (
               f"{lsm_exp}/{lsm_mod}/{lsm_stp}/{yyyy_mm}/"
               f"{lsm_exp}_{lsm_mod}_{lsm_stp}_{yyyy_mm}_utc.nc4"
               )
            local_path = f"/tmp/{os.path.basename(ldas_file_key)}"

            if not rrr_io_drv.drv_s3_file_exists(s3_name, ldas_file_key):
                # *************************************************************
                # driver: download
                # *************************************************************
                t_ed_dwnld_start = time.time()
                rrr_drv.drv_dwn(rrr)
                t_ed_dwnld_end = time.time()
                ed_dwnld_runtime = t_ed_dwnld_end - t_ed_dwnld_start
                print("Download driver: done")

                # *************************************************************
                # driver: lsm
                # *************************************************************
                t_lsm_start = time.time()
                rrr_drv.drv_lsm(rrr)
                t_lsm_end = time.time()
                lsm_runtime = t_lsm_end - t_lsm_start
                print("LSM driver: done")

                # Upload ldas files (3H) to S3
                t_s3_upld1_start = time.time()
                for root, dirs, files in os.walk(ldas_fldr):
                    for filename in files:
                        file_path = os.path.join(root, filename)
                        if rrr_io_drv.drv_upl_S3(s3_name, file_path,
                                                 basin_id, lsm_exp,
                                                 lsm_mod, lsm_stp,
                                                 yyyy_mm, 'LDAS'):
                            rrr_io_drv.drv_del_file(file_path)
                rrr_io_drv.drv_del_folder(ldas_fldr)
                print(
                    f"All contents of {ldas_fldr} have been uploaded "
                    "and deleted successfully."
                    )
                t_s3_upld1_end = time.time()
                s3_upld1_runtime = t_s3_upld1_end - t_s3_upld1_start
            else:
                print(
                    f"Skipping download and LSM drivers for {ldas_file_key} "
                    "as it already exists in S3."
                    )
                # File exists in S3, download it to /tmp
                t_s3_dwnld_start = time.time()
                s3_client = boto3.client('s3')
                try:
                    s3_client.download_file(s3_name, ldas_file_key, local_path)
                    print(f"File downloaded from S3 to {local_path}")
                except Exception as e:
                    print(f"Error downloading file from S3: {e}")
                t_s3_dwnld_end = time.time()
                s3_dwnld_runtime = t_s3_dwnld_end - t_s3_dwnld_start
            # *****************************************************************
            # driver: volume
            # *****************************************************************
            t_zen_start = time.time()
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
            t_zen_end = time.time()
            zen_runtime = t_zen_end - t_zen_start

            t_vol_start = time.time()
            rrr_drv.drv_vol(rrr)
            print("Volume driver: done")
            t_vol_end = time.time()
            vol_runtime = t_vol_end - t_vol_start

            # *****************************************************************
            # Define file paths and upload to S3 bucket
            # *****************************************************************
            m3_file = (
                f"/tmp/m3_riv_pfaf_{basin_id}_{lsm_exp}_{lsm_mod}_"
                f"{lsm_stp}_{yyyy_mm}_utc.nc4"
                )
            ldas_file = f'/tmp/{lsm_exp}_{lsm_mod}_{lsm_stp}_{yyyy_mm}_utc.nc4'

            # Upload files
            t_s3_upld2_start = time.time()
            files_to_upload = [(m3_file, 'm3'), (ldas_file, 'LDAS')]
            for file_path, label in files_to_upload:
                if os.path.exists(file_path):
                    if label == 'm3' or (
                            label == 'LDAS' and
                            not rrr_io_drv.drv_s3_file_exists(s3_name,
                                                              ldas_file_key)
                            ):
                        try:
                            rrr_io_drv.drv_upl_S3(s3_name, file_path, basin_id,
                                                  lsm_exp, lsm_mod, lsm_stp,
                                                  yyyy_mm, label)
                            print(f"{label} file uploaded successfully.")
                            rrr_io_drv.drv_del_file(file_path)
                        except Exception as e:
                            print(f"Failed to upload {label} file: {e}")
                else:
                    print(
                        f"{label} file not found at {file_path}, "
                        "skipping upload."
                        )
            t_s3_upld2_end = time.time()
            s3_upld2_runtime = t_s3_upld2_end - t_s3_upld2_start

    s3_upld_runtime = s3_upld1_runtime + s3_upld2_runtime
    t_end = time.time()
    total_runtime = t_end - t_start
    max_mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    print(
        f"[Profiling] Total RunTime: "
        f"{total_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] Earthdata download RunTime: "
        f"{ed_dwnld_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] Zenodo file handling Time: "
        f"{zen_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] LSM driver Time: "
        f"{lsm_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] Volume driver Time: "
        f"{vol_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] S3 download (monthly LDAS file) Time: "
        f"{s3_dwnld_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] S3 upload 1 (3-hourly LDAS files) Time: "
        f"{s3_upld1_runtime:.2f} seconds"
        )
    print(
        f"[Profiling] S3 upload 2 (m3 file and/or monthly LDAS file) Time: "
        f"{s3_upld2_runtime:.2f} seconds"
        )
    print(f"[Profiling] Max Memory Usage: {max_mem_mb:.2f} MB")

    return {
        'status': 'Success',
        'profiling': {
            'runtime_total_sec': total_runtime,
            'runtime_ed_dwnld_sec': ed_dwnld_runtime,
            'runtime_zen_sec': zen_runtime,
            'runtime_lsm_sec': lsm_runtime,
            'runtime_vol_sec': vol_runtime,
            'runtime_s3_dwnld_sec': s3_dwnld_runtime,
            'runtime_s3_upld_sec': s3_upld_runtime,
            'memory_max_MB': max_mem_mb
        }
    }


# *****************************************************************************
# End
# *****************************************************************************
