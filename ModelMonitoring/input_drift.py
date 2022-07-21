#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
This file is automatically generated by AION for AION_37_1 usecase.
File generation time: 2022-07-19 11:45:42
'''
#Standard Library modules
import sys
import json
import platform

#Third Party modules
import mlflow
import numpy as np 
import pandas as pd 
from scipy import stats as st 
from pathlib import Path
        
class inputdrift():        
        
    def __init__(self,base_config):
        if base_config['inputUri']:	
            self.usecase = base_config['modelName'] + '_' + base_config['modelVersion']        
            self.currentDataLocation = base_config['currentDataLocation']        
            home = Path.home()        
            if platform.system() == 'Windows':        
                from pathlib import WindowsPath        
                output_data_dir = WindowsPath(home)/'AppData'/'Local'/'HCLT'/'AION'/'Data'        
                output_model_dir = WindowsPath(home)/'AppData'/'Local'/'HCLT'/'AION'/'target'/self.usecase        
            else:        
                from pathlib import PosixPath        
                output_data_dir = PosixPath(home)/'HCLT'/'AION'/'Data'        
                output_model_dir = PosixPath(home)/'HCLT'/'AION'/'target'/self.usecase        
            if not output_model_dir.exists():        
                raise ValueError(f'Configuration file not found at {output_model_dir}')        
        
            tracking_uri = 'file:///' + str(Path(output_model_dir)/'mlruns')        
            registry_uri = 'sqlite:///' + str(Path(output_model_dir)/'mlruns.db')        
            mlflow.set_tracking_uri(tracking_uri)        
            mlflow.set_registry_uri(registry_uri)        
            client = mlflow.tracking.MlflowClient(        
                tracking_uri=tracking_uri,        
                registry_uri=registry_uri,        
                )        
            model_version_uri = 'models:/{model_name}/production'.format(model_name=self.usecase)        
            model = mlflow.pyfunc.load_model(model_version_uri)        
            run = client.get_run(model.metadata.run_id)        
            if run.info.artifact_uri.startswith('file:'):        
                artifact_path = Path(run.info.artifact_uri[len('file:///') : ])        
            else:        
                artifact_path = Path(run.info.artifact_uri)        
            self.trainingDataPath = artifact_path/(self.usecase + '_data.csv')        
        
    def get_input_drift(self,current_data, historical_data):        
        curr_num_feat = current_data.select_dtypes(include='number')        
        hist_num_feat = historical_data.select_dtypes(include='number')        
        num_features = [feat for feat in historical_data.columns if feat in curr_num_feat]        
        alert_count = 0        
        data = {        
            'current':{'data':current_data},        
            'hist': {'data': historical_data}        
            }        
        dist_changed_columns = []        
        dist_change_message = []        
        for feature in num_features:        
            cumulative_data = hist_num_feat[feature]        
            cumulative_data = cumulative_data.append(curr_num_feat[feature], ignore_index=True)        
            curr_static_value = round(st.ks_2samp( hist_num_feat[feature], curr_num_feat[feature]).pvalue,3)        
            cum_static_value = round(st.ks_2samp( cumulative_data, hist_num_feat[feature]).pvalue,3)
            if (curr_static_value < 0.05 and  cum_static_value < 0.05):        
                distribution = {}        
                distribution['hist'] = self.DistributionFinder( historical_data[feature])        
                distribution['curr'] = self.DistributionFinder( current_data[feature])        
                distribution['cum'] = self.DistributionFinder( cumulative_data)        
                if(distribution['hist']['name'] == distribution['curr']['name'] or  distribution['hist']['name'] == distribution['cum']['name']):        
                    pass        
                else:        
                    alert_count = alert_count + 1        
                    dist_changed_columns.append(feature)        
                    changed_column = {}        
                    changed_column['Feature'] = feature        
                    changed_column['KS_Training'] = curr_static_value        
                    changed_column['KS_Cumulative'] = cum_static_value        
                    changed_column['Training_Distribution'] = distribution['hist']['name']        
                    changed_column['New_Distribution'] = distribution['curr']['name']        
                    changed_column['Cumulative_Distribution'] = distribution['cum']['name']        
                    dist_change_message.append(changed_column)        
        if alert_count:        
            resultStatus = dist_change_message        
        else :        
            resultStatus='Model is working as expected'        
        return(alert_count, resultStatus)        
        
    def DistributionFinder(self,data):        
        best_distribution =''        
        best_sse =0.0        
        if(data.dtype in ['int','int64']):        
            distributions= {'bernoulli':{'algo':st.bernoulli},        
                            'binom':{'algo':st.binom},        
                            'geom':{'algo':st.geom},        
                            'nbinom':{'algo':st.nbinom},        
                            'poisson':{'algo':st.poisson}        
                            }        
            index, counts = np.unique(data.astype(int),return_counts=True)        
            if(len(index)>=2):        
                best_sse = np.inf        
                y1=[]        
                total=sum(counts)        
                mean=float(sum(index*counts))/total        
                variance=float((sum(index**2*counts) -total*mean**2))/(total-1)        
                dispersion=mean/float(variance)        
                theta=1/float(dispersion)        
                r=mean*(float(theta)/1-theta)        
        
                for j in counts:        
                        y1.append(float(j)/total)        
                distributions['bernoulli']['pmf'] = distributions['bernoulli']['algo'].pmf(index,mean)        
                distributions['binom']['pmf'] = distributions['binom']['algo'].pmf(index,len(index),p=mean/len(index))        
                distributions['geom']['pmf'] = distributions['geom']['algo'].pmf(index,1/float(1+mean))        
                distributions['nbinom']['pmf'] = distributions['nbinom']['algo'].pmf(index,mean,r)        
                distributions['poisson']['pmf'] = distributions['poisson']['algo'].pmf(index,mean)        
        
                sselist = []        
                for dist in distributions.keys():        
                    distributions[dist]['sess'] = np.sum(np.power(y1 - distributions[dist]['pmf'], 2.0))        
                    if np.isnan(distributions[dist]['sess']):        
                        distributions[dist]['sess'] = float('inf')        
                best_dist = min(distributions, key=lambda v: distributions[v]['sess'])        
                best_distribution = best_dist        
                best_sse = distributions[best_dist]['sess']        
        
            elif (len(index) == 1):        
                best_distribution = 'Constant Data-No Distribution'        
                best_sse = 0.0        
        elif(dataType == 'float64'):        
            distributions = [st.uniform,st.expon,st.weibull_max,st.weibull_min,st.chi,st.norm,st.lognorm,st.t,st.gamma,st.beta]        
            best_distribution = st.norm.name        
            best_sse = np.inf        
            nrange = data.max() - data.min()        
        
            y, x = np.histogram(data.astype(float), bins='auto', density=True)        
            x = (x + np.roll(x, -1))[:-1] / 2.0        
        
            for distribution in distributions:        
                with warnings.catch_warnings():        
                    warnings.filterwarnings('ignore')        
                    params = distribution.fit(data.astype(float))        
                    arg = params[:-2]        
                    loc = params[-2]        
                    scale = params[-1]        
                    pdf = distribution.pdf(x, loc=loc, scale=scale, *arg)        
                    sse = np.sum(np.power(y - pdf, 2.0))        
                    if( sse < best_sse):        
                        best_distribution = distribution.name        
                        best_sse = sse        
        
        return {'name':best_distribution, 'sse': best_sse}        
        
        
def check_drift( config):        
    inputdriftObj = inputdrift(config)        
    historicaldataFrame=pd.read_csv(inputdriftObj.trainingDataPath)        
    currentdataFrame=pd.read_csv(inputdriftObj.currentDataLocation)        
    dataalertcount,message = inputdriftObj.get_input_drift(currentdataFrame,historicaldataFrame)        
    if message == 'Model is working as expected':        
        output_json = {'status':'SUCCESS','data':{'Message':'Model is working as expected'}}        
    else:        
        output_json = {'status':'SUCCESS','data':{'Affected Columns':message}}        
    return(output_json)        
