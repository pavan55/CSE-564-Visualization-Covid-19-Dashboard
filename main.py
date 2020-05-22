import json
import glob
import sys
import datetime
import numpy as np
import pandas as pd
import pylab as plt
from flask import Flask,render_template
from flask import request
from sodapy import Socrata
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/hospitals", methods = ['POST','GET'])
def gethospitals():
    df = pd.read_csv('static/data/HospitalBedsIndia.csv')
    cols = json.dumps(list(df.columns))
    df = df.fillna(int(0))
    rows = json.dumps(df.to_dict(orient='records'), indent=2)
    data = { 'rows': rows, 'cols': cols}
    return data

@app.route("/getconfirmedcases",methods = ['POST','GET'])
def stackedarea():
    start,end = 25,40
    import pandas as pd
    df = pd.read_csv('static/data/covid_19_india.csv')
    states = df['State/UnionTerritory'].unique()
    regions,confirmed = [df[df['State/UnionTerritory'] == s] for s in states],[]
    for i,s in enumerate(states):
        cnfrmed = list(regions[i][end-1:end].Confirmed)
        if len(cnfrmed) == 0: continue
        confirmed.append((cnfrmed[0],s,i))
    confirmed = sorted(confirmed,reverse=True)
    #Top 10 state ids
    stateids = [k for i,j,k in confirmed[:10]]
    states = [j for i,j,k in confirmed[:10]]
    cnt = [ list(regions[i][start:end].Confirmed) for i in stateids]
    df = pd.DataFrame()
    for i,s in enumerate(states):
        df[s] = cnt[i]
    cols = json.dumps(list(df.columns))
    df['total'] = np.sum(cnt,axis=0)
    df['day'] = range(end-start)
    rows = json.dumps(df.to_dict(orient='records'), indent=2)
    data = { 'rows': rows, 'cols': cols}
    return data


# @app.route("/get_time_series_data/<state>/<column>")
# def time_series_data(state, column):
#     isaggr = request.args.get('aggr', False)
#     startDate = request.args.get('startDate', '01/01/2020') or '01/01/2020'
#     endDate = request.args.get('endDate', '5/20/2020') or '5/20/2020'
#     startDate = datetime.datetime.strptime(startDate, '%m/%d/%Y')
#     endDate = datetime.datetime.strptime(endDate, '%m/%d/%Y')
#
#     print(startDate, endDate)
#     df_aggr = pd.read_csv('static/data/covid19_usa_complete.csv')
#     if state!='' and state!='all':
#         df_aggr = df_aggr[df_aggr.name == state]
#     df_aggr = df_aggr.sort_values('Last Update')
#     df_aggr['date'] = df_aggr['Last Update'].map(lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
#     datecheck = (df_aggr['date'] >= startDate) & (df_aggr['date'] <= endDate)
#     df_aggr = df_aggr[datecheck]
#     if not isaggr:
#         if state == 'all':
#             df_aggr =  df_aggr.groupby(['date']).sum()
#             return {"values":df_aggr[column].tolist(), "dates": df_aggr.index.map(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d') ).tolist()}
#         return {"values": df_aggr[column].tolist(), "dates": df_aggr['Last Update'].map(lambda x: x[:10]).tolist()}
#     return str(df_aggr[column].sum())

@app.route("/get_time_series_data/<state>/<column>")
def time_series_data(state, column):
    isaggr = request.args.get('aggr', False)
    startDate = request.args.get('startDate', '3/2/2020') or '3/2/2020'
    endDate = request.args.get('endDate', '5/14/2020') or '5/14/2020'
    startDate = datetime.datetime.strptime(startDate, '%m/%d/%Y')
    endDate = datetime.datetime.strptime(endDate, '%m/%d/%Y')

    print(startDate, endDate)
    df_aggr = pd.read_csv('static/data/covid19_usa_complete.csv')
    if state!='' and state!='all':
        df_aggr = df_aggr[df_aggr.name == state]
    # df_aggr = df_aggr.sort_values('Last Update')
    df_aggr['date'] = df_aggr['Last Update'].map(lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
    # if aggregated data is requested
    if isaggr:
        if state != 'all':
            return str(df_aggr[df_aggr.date == endDate][column].max() - df_aggr[df_aggr.date == startDate][column].max())
        return str(df_aggr[df_aggr.date == endDate].groupby('name')[column].max().sum() - df_aggr[df_aggr.date == startDate].groupby('name')[column].max().sum())

    daterange = (df_aggr['date'] >= startDate) & (df_aggr['date'] <= endDate)
    df_aggr = df_aggr[daterange]
    df_aggr = df_aggr.sort_values('date')
    if state == 'all':
        df_aggr = df_aggr.groupby(['date', 'name'])[column].max().reset_index()
        df_day = df_aggr.groupby('date')[column].sum().diff()[1:]
        return {"values": [abs(x) for x in df_day.tolist()],
                "dates": df_day.index.map(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d')).tolist()}

    df_day = df_aggr.groupby('date')[column].max().diff()[1:]
    return {"values": df_day.tolist(), "dates": df_day.index.map(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d')).tolist()}


@app.route("/get_map_data")
def get_map_data():
    startDate = request.args.get('startDate', '01/01/2020') or '01/01/2020'
    endDate = request.args.get('endDate', '5/20/2020') or '5/20/2020'
    startDate = datetime.datetime.strptime(startDate, '%m/%d/%Y')
    endDate = datetime.datetime.strptime(endDate, '%m/%d/%Y')

    print(startDate, endDate, request.args.get('startDate'), request.args.get('endDate'))
    df_aggr = pd.read_csv('static/data/covid19_usa_complete.csv')
    df_aggr = df_aggr.rename(columns = {'name':'states'})
    # if state!='' and state!='all':
    #     df_aggr = df_aggr[df_aggr.states == state]
    df_aggr = df_aggr.sort_values('Last Update')
    df_aggr['date'] = df_aggr['Last Update'].map(lambda x: datetime.datetime.strptime(x[:10], '%Y-%m-%d'))
    datecheck = (df_aggr['date'] >= startDate) & (df_aggr['date'] <= endDate)
    df_aggr = df_aggr[datecheck]
    df_aggr = df_aggr.groupby('states').agg({'Confirmed': 'sum', 'Deaths': 'sum', 'Recovered': 'sum', 'Region': 'any'})
    # print(df_aggr)
    return df_aggr[['Confirmed', 'Deaths', 'Recovered']].to_csv(header=True)

@app.route("/get_radar_data/<state>")
def get_radar_data(state):
    global results_df
    fraction = request.args.get('fraction', 'True') or 'True'
    fraction = True if fraction == 'True' else False
    if state == 'all':
        state = 'United States'
    # if state != 'all':
    df_male = results_df[(results_df.sex == 'Male') & (results_df.state == state)][['age_group', 'covid_19_deaths']].fillna(0)
    df_male = df_male.rename(columns = {'age_group' : 'axis', 'covid_19_deaths': 'value'})
    df_male['value'] = df_male['value'].astype('int')

    df_female = results_df[(results_df.sex == 'Female') & (results_df.state == state)][['age_group', 'covid_19_deaths']].fillna(0)
    df_female = df_female.rename(columns={'age_group': 'axis', 'covid_19_deaths': 'value'})
    df_female['value'] = df_female['value'].astype('int')
    if not fraction:
        return { 'male' : df_male.to_dict('records'), 'female' : df_female.to_dict('records')}
    df_male['value'] = df_male['value']/ df_male['value'].sum()
    df_female['value'] = df_female['value'] / df_female['value'].sum()
    return {'male': df_male.to_dict('records'), 'female': df_female.to_dict('records')}


client = Socrata("data.cdc.gov", None)
results = client.get("9bhg-hcku", limit=2000)
results_df = pd.DataFrame.from_records(results)

if __name__ == "__main__":
    app.run('localhost', '5050')
