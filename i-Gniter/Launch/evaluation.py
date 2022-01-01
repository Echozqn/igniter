#!/usr/bin/env python3

import argparse
import logging
import json
import os
import numpy as np

model_path = "./model/model"
save_dir = "./perf_data"

def slo_vio(file_path, slo, strip_time):
    start  = strip_time * 1e9
    end = strip_time * 1e9
    
    slo = slo * 2 * 1e6

    request_start = []
    latency = []

    with open(file_path) as f:
        for line in f:
            eles = line.split(",")
            request_start.append(int(eles[1]))
            latency.append(int(eles[4]))
    start_time = np.min(request_start) + start
    end_time = np.max(request_start) - end

    total_count = 0
    slo_vio_count = 0

    for i in range(len(request_start)):
        if request_start[i] > start_time and request_start[i] < end_time:
            total_count +=1
            if latency[i] > slo:
                slo_vio_count += 1

    return (100.0 * slo_vio_count / total_count)

def durationps(openfilepath):
    with open(openfilepath) as f:
        log = f.readlines()
        data = log[1].split(",")
        throughout_per_second = float(data[1])
        gpu_lantency_ms = int(data[6]) / 1000
        avg_lantency_ms = (int(data[5]) + int(data[6]) + int(data[7])) / 1000
        return throughout_per_second, gpu_lantency_ms, avg_lantency_ms
    

def get_perf_file(model, resource, batch):
    perf_file = model + "_" + str(resource) + "_" + str(batch) + ".csv"
    return perf_file

def get_slo_file(model, resource, batch):
    perf_file = get_perf_file(model, resource, batch)
    return "slo_" + perf_file

if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument(
        "-c",
        "--config-file",
        type=str,
        default="config.json",
        help="Config file must be a json file. Write the models you want to evaluate with config. "
    )
    parse.add_argument(
        "-t",
        "--time-5s",
        type=int,
        default=16,
        help="The time(* 5s) each model will running to get the lantency and throught data. "
    )
    parse.add_argument(
        "-s",
        "--strip-time",
        type=float,
        default=10,
        help="The time(s) before and after measure slo_vio. "
    )
    parse.add_argument(
        "-i",
        "--input_data",
        type=str,
        default=None,
        help="The directory of the data for inference. "
    )

    FLAGES = parse.parse_args()
    os.system("./clear.py -l")

    model_path = os.path.abspath(model_path)
    save_dir = os.path.abspath(save_dir)
    

    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
                        datefmt='%a %d %b %Y %H:%M:%S', filename='evaluation.log', filemode='a')

    time_5s = FLAGES.time_5s
    config_file = FLAGES.config_file
    strip_time = FLAGES.strip_time
    input_data = FLAGES.input_data


    with open(config_file) as f:
        config = json.load(f)

    models = config.get("models")
    rates = config.get("rates")
    slos = config.get("slos")
    resources = config.get("resources")
    batches = config.get("batches")

    if models is None or rates is None or slos is None or resources is None or batches is None:
        logging.error("Config error. ")
        exit()

    length = len(models)
    cmd = "./test_inference.py "
    for i in range(length):
        cmd += "-m " + models[i] + ":" + str(resources[i]) + \
            ":" + str(batches[i]) + ":" + str(rates[i]) + " "
    cmd += "-t {} ".format(time_5s)
    cmd += "-r " + model_path + " "
    cmd += "-s " + save_dir + " "
    if input_data is not None:
        cmd += "-i " + input_data + " "
    os.system(cmd)
    logging.info(cmd)

    for i in range(length):
        perf_file = get_perf_file(models[i], resources[i], batches[i])
        perf_file = os.path.join(os.path.join(save_dir, str(i + 1)), perf_file)

        slo_file = get_slo_file(models[i], resources[i], batches[i])
        slo_file = os.path.join(os.path.join(save_dir, str(i + 1)), slo_file)

        print(models[i] + ":" + str(resources[i]) + " " + str(batches[i]))

        print("[throughout_per_second, gpu_lantency_ms, avg_lantency_ms]: {}".format(durationps(perf_file)))

        print("slo_vio: {}".format(slo_vio(slo_file, slos[i], strip_time)))