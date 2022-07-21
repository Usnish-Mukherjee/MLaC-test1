#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This file is automatically generated by AION for AION_37_1 usecase.
File generation time: 2022-07-19 11:45:38
'''
#Standard Library modules
import json
import argparse
import platform
import logging

#Third Party modules
from pathlib import Path
import pandas as pd 

input_file = {
    "rawData": "rawData.dat",
    "prodGrndTruData": "prodGrndTruData.dat",
    "prodData": "prodData.dat"
}
output_file = {
    "metaData": "modelMetaData.json",
    "log": "aion.log",
    "outputData": "rawData.dat"
}
                    
def read_json(file_path):                    
    data = None                    
    with open(file_path,'r') as f:                    
        data = json.load(f)                    
    return data                    
                    
def write_json(data, file_path):                    
    with open(file_path,'w') as f:                    
        json.dump(data, f)                    
                    
def read_data(file_path, encoding='utf-8', sep=','):                    
    return pd.read_csv(file_path, encoding=encoding, sep=sep)                    
                    
def write_data(data, file_path, index=False):                    
    return data.to_csv(file_path, index=index)                    
                    
#Uncomment and change below code for google storage                    
#def write_data(data, file_path, index=False):                    
#    file_name= file_path.name                    
#    data.to_csv('output_data.csv')                    
#    storage_client = storage.Client()                    
#    bucket = storage_client.bucket('aion_data')                    
#    bucket.blob('prediction/'+file_name).upload_from_filename('output_data.csv', content_type='text/csv')                    
#    return data                    
                    
def is_file_name_url(file_name):                    
    supported_urls_starts_with = ('gs://','https://','http://')                    
    return file_name.startswith(supported_urls_starts_with)                    

                    
log = None                    
def set_logger(log_file, mode='a'):                    
    global log                    
    logging.basicConfig(filename=log_file, filemode=mode, format='%(asctime)s %(name)s- %(message)s', level=logging.INFO, datefmt='%d-%b-%y %H:%M:%S')                    
    log = logging.getLogger(Path(__file__).parent.name)                    
    return log                    
                    
def get_logger():                    
    return log

                    
def log_dataframe(df, msg=None):                    
    import io                    
    buffer = io.StringIO()                    
    df.info(buf=buffer)                    
    if msg:                    
        log_text = f'Data frame after {msg}:'                    
    else:                    
        log_text = 'Data frame:'                    
    log_text += '\n\t'+str(df.head(2)).replace('\n','\n\t')                    
    log_text += ('\n\t' + buffer.getvalue().replace('\n','\n\t'))                    
    get_logger().info(log_text)
        
def validateConfig(base_config):        
    config_file = Path(__file__).parent/'config.json'        
    if not Path(config_file).exists():        
        raise ValueError(f'Config file is missing: {config_file}')        
    config = read_json(config_file)        
    if not base_config['inputDataLocation']:		
        if config['inputDataLocation'] != '<input data location>' and config['inputDataLocation'] != '':		
            base_config['inputDataLocation'] = config['inputDataLocation']		
        elif not base_config['inputPath']:        
            raise ValueError('Please provide dataset path using -l (for data location ) or -i (for folder) command line argument')        
        
    if not base_config['outputPath']:        
        base_config['outputPath'] = config['outputPath']        
		
    if base_config['inputDataLocation']:        
        if not Path(base_config['inputDataLocation']).exists():        
            if not is_file_name_url(base_config['inputDataLocation']):        
                loc = base_config['inputDataLocation']        
                raise ValueError(f'Data location does not exists: {loc}')        
    config = read_json(config_file)        
    return base_config, config

#This function will read the data and save the data on persistent storage        
def load_data(base_config):        
        
    base_config, config = validateConfig(base_config)
    outputPath = Path(base_config['outputPath'])        
    outputPath.mkdir(parents=True, exist_ok=True)	
    log_file = outputPath/output_file['log']        
    logger = set_logger(log_file)
    if base_config['inputPath']:
        location = Path(base_config['inputPath'])
        actual_data_location = Path(base_config['inputPath'])/input_file['prodGrndTruData']
        predict_data_location = Path(base_config['inputPath'])/input_file['prodData']
        raw_data_location = Path(base_config['inputPath'])/input_file['rawData']		
        if actual_data_location.exists() and predict_data_location.exists(): 		
            predicted_data = pd.read_csv(predict_data_location)        		
            actual_data_path = pd.read_csv(actual_data_location)
            common_col = [k for k in predicted_data.columns.tolist() if k in actual_data_path.columns.tolist()]				
            mergedRes = pd.merge(actual_data_path, predicted_data, on =common_col,how = 'inner')
            raw_data_path = pd.read_csv(raw_data_location)			
            df = pd.concat([raw_data_path,mergedRes])
        else:
            location = base_config['inputDataLocation']
            get_logger().info(f'Dataset path: {location}')        
            df = read_data(location)			
    else:
        location = base_config['inputDataLocation']
        get_logger().info(f'Dataset path: {location}')        
        df = read_data(location)             
    status = {}        
    output_data_path = str(outputPath/output_file['outputData'])        
    log_dataframe(df)        
    required_features = config['selected_features'] + [config['target_feature']]        
    get_logger().info('Dataset features required: ' + ','.join(required_features))        
    missing_features = [x for x in required_features if x not in df.columns.tolist()]        
    if missing_features:        
        raise ValueError(f'Some feature/s is/are missing: {missing_features}')        
    get_logger().info('Removing unused features: '+','.join(list(set(df.columns) - set(required_features))))        
    df = df[required_features]        
    get_logger().info(f'Required features: {required_features}')        
    try:        
        get_logger().info(f'Saving Dataset: {output_data_path}')        
        write_data(df, output_data_path, index=False)        
        status = {'Status':'Success','DataFilePath':output_file['outputData']}        
    except:        
        raise ValueError('Unable to create data file')        
        
    meta_data_file = outputPath/output_file['metaData']        
    meta_data = dict()        
    meta_data['usecase'] = config['modelName'] + '_' + config['modelVersion']        
    meta_data['load_data'] = {}        
    meta_data['load_data']['selected_features'] = [x for x in config['selected_features'] if x != config['target_feature']]        
    meta_data['load_data']['Status'] = status        
    write_json(meta_data, meta_data_file)        
    output = json.dumps(status)        
    get_logger().info(output)        
    return output

        
if __name__ == '__main__':        
    parser = argparse.ArgumentParser()        
    parser.add_argument('-i', '--inputPath', help='path of the input data')        
    parser.add_argument('-l', '--inputDataLocation', help='uri for the input data')        
    parser.add_argument('-o', '--outputPath', help='path for saving the output data')        
        
    args = parser.parse_args()        
        
    config = {'inputPath':None, 'outputPath':None,'inputDataLocation':None}        
        
    if args.inputPath:        
        config['inputPath'] = args.inputPath        
    if args.inputDataLocation: #uri has higher preference than input path        
        config['inputDataLocation'] = args.inputDataLocation        
    if args.outputPath:        
        config['outputPath'] = args.outputPath        
        
    try:        
        print(load_data(config))        
    except Exception as e:        
        get_logger().error(e, exc_info=True)        
        status = {'Status':'Failure','Message':str(e)}        
        print(json.dumps(status))        