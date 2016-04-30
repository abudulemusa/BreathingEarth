import datetime
import sys
import utils
import datetime
import json
import pandas as pd

def select_sites_that_have_data_on_date(df, start_date):
    ''' Returns a dataframe containing only sites that
    have data on start_date.  The value of the vertical
    position on that date is then used as a reference date
    and is subtracted from all other values for that site.
    Date in format 'YYYY-MM-DD' '''
    # Select sites
    # Only use values that start on or after start_date
    df = df.loc[(df.datetime >= start_date)]
    selected_sites = df.loc[(df.datetime == start_date)]
    selected_df = pd.DataFrame(columns = df.columns)
    for s in selected_sites.site.unique():
        # Get value of du at start date
        zero_du = df.loc[(df.datetime == start_date) & (df.site == s)]['du'].unique()
        # Only collect information on the site
        site_df = df.loc[df.site == s]
        # Create an adjusted du column, that subtracts the vertical position
        # on the first day
        site_df['adj_du'] = site_df['du'] - zero_du[0]
        selected_df = selected_df.append(site_df)
    return selected_df

def get_dates(start_date, sample_size):
    '''Sample size is in days'''
    now = datetime.datetime.now()
    start_datetime = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    time_list = []; t = start_datetime
    while t < now:
        time_list.append(datetime.datetime.strftime(t, '%Y-%m-%d'))
        t = t + datetime.timedelta(days = sample_size)
    return time_list

def sample_df(selected_df, sample_size, start_date):
    time_list = get_dates(start_date, sample_size)
    sample_df = pd.DataFrame(columns = selected_df.columns)
    for t in time_list:
        sample_df = sample_df.append(selected_df.loc[selected_df.datetime == t])
    return sample_df


def make_json(df, coords, sample_size):
    grouped = df.groupby('datetime')
    du_dict = {}
    for a, groupdf in grouped:
        grp_time = a.strftime('%Y-%m-%d')
        du_dict[grp_time] = {}
        for s in groupdf.site:
            adj_du = groupdf.loc[groupdf.site == s]['adj_du'].values[0]
            coord = coords[s]
            du_dict[grp_time].update({s: {'adj_du': adj_du,
                                      'coordinates' : coord }})
    filename = '../../data/positions_sample_size_{0}.json'.format(str(sample_size))
    with open(filename, 'w') as f:
        json.dump(du_dict, f)
    return json.dumps(du_dict)

def run(start_date = '2008-01-01', sample_size = 30):
    conn = utils.get_dynamo_conn()
    df = utils.get_medians_df(conn)
    selected_df = select_sites_that_have_data_on_date(df, start_date)
    sample_df = sample_df(selected_df, sample_size, start_date)
    coords = utils.get_dict_of_coordinates(conn, sample_df.site.unique())
    du_json = make_json(sample_df, coords, sample_size)