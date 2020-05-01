import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.colors
from collections import OrderedDict
import requests


# default list of all countries of interest
country_default = OrderedDict([('Canada', 'CAN'), ('United States', 'USA'),
  ('Brazil', 'BRA'), ('France', 'FRA'), ('India', 'IND'), ('Italy', 'ITA'),
  ('Germany', 'DEU'), ('United Kingdom', 'GBR'), ('China', 'CHN'), ('Japan', 'JPN')])


def return_figures(countries=country_default, st_date = 1990, end_date = 2014):
    """Creates four plotly visualizations using the World Bank API

    # Example of the World Bank API endpoint:
    # arable land for the United States and Brazil from 1990 to 2015
    # http://api.worldbank.org/v2/countries/usa;bra/indicators/AG.LND.ARBL.HA?date=1990:2015&per_page=1000&format=json

    Args:
        country_default (dict): list of countries for filtering the data
        st_date (int): first year to be considered
        end_date (int): last year to be considered

    Returns:
        list (dict): list containing the plotly visualizations

    """

    # when the countries variable is empty, use the country_default dictionary
    if not bool(countries):
        countries = country_default

    # prepare filter data for World Bank API
    # the API uses ISO-3 country codes separated by ;
    country_filter = list(countries.values())
    country_filter = [x.lower() for x in country_filter]
    country_filter = ';'.join(country_filter)

    # World Bank indicators of interest for pulling data

    indicators = ['EG.FEC.RNEW.ZS', 'EN.ATM.CO2E.PC', 'EN.ATM.CO2E.KT',\
                  'AG.LND.FRST.K2', 'NY.GDP.TOTL.RT.ZS']

    data_frames = [] # stores the data frames with the indicator data of interest
    urls = [] # url endpoints for the World Bank API
    graphs = [[] for i in range(8)] # stores graphs
    layouts = [[] for i in range(8)] # stores layouts

    # pull data from World Bank API and clean the resulting json
    # results stored in data_frames variable
    for indicator in indicators:
        url = 'http://api.worldbank.org/v2/countries/' + country_filter +\
        '/indicators/' + indicator + '?date=' + str(st_date) + ':' +\
        str(end_date) + '&per_page=1000&format=json'

        urls.append(url)

        try:
            r = requests.get(url)
            data = r.json()[1]
        except:
            print('could not load data ', indicator)

        for value in data:
            value['indicator'] = value['indicator']['value']
            value['country'] = value['country']['value']

        data_frames.append(data)

    # 0) EG.FEC.RNEW.ZS = Renewable energy consumption (% of total final energy consumption)
    df_renewable = pd.DataFrame(data_frames[0])
    # 1) EN.ATM.CO2E.PC = CO2 emissions (metric tons per capita)
    df_CO2_per_capita = pd.DataFrame(data_frames[1])
    # 2) EN.ATM.CO2E.KT = CO2 emissions (kt)
    df_CO2_tot = pd.DataFrame(data_frames[2])
    # 3) AG.LND.FRST.K2 = Forest area (sq. km)
    df_forest = pd.DataFrame(data_frames[3])
    # 4) NY.GDP.TOTL.RT.ZS = Total natural resources rents (% of GDP)
    df_resources_rent = pd.DataFrame(data_frames[4])




    # first chart plots CO2 emissions (metric tons per capita) from st_date to end_date

    # this  country list is re-used by all the charts to ensure legends have the same
    # order and color
    countrylist = df_CO2_per_capita.country.unique().tolist()

    # filtering plots the countries in decreasing order by their values
    df_CO2_per_capita.sort_values('date', ascending=True, inplace=True)

    for country in countrylist:
        x_val = df_CO2_per_capita[df_CO2_per_capita['country'] == country].date.tolist()
        y_val =  df_CO2_per_capita[df_CO2_per_capita['country'] == country].value.tolist()
        graphs[0].append(go.Scatter(x = x_val, y = y_val, mode = 'lines', name = country))

    layouts[0] = dict(title = 'CO2 emissions per capita',
                xaxis = dict(title = 'Year'),
                yaxis = dict(title = 'Metric tons'), )

    # second chart plots CO2 emissions (metric tons per capita) for end_date as a bar chart
    df_CO2_per_capita.sort_values('value', ascending=True, inplace=True)
    df_CO2_per_capita = df_CO2_per_capita[df_CO2_per_capita['date'] == str(end_date)]

    graphs[1].append( go.Bar(x = df_CO2_per_capita.country.tolist(), y = df_CO2_per_capita.value.tolist(),))

    layouts[1] = dict(title = 'CO2 emissions per capita in ' + str(end_date),
                xaxis = dict(title = 'Country',),
                yaxis = dict(title = 'metric tons'), )


    # third chart plots CO2 emission vs forestal area
    df_CO2_tot_to_forest = df_CO2_tot.merge(df_forest, on=['country', 'date'])
    df_CO2_tot_to_forest.sort_values('date', ascending=True, inplace=True)

    plotly_default_colors = plotly.colors.DEFAULT_PLOTLY_COLORS

    for i, country in enumerate(countrylist):

        current_color = []

        x_val = df_CO2_tot_to_forest[df_CO2_tot_to_forest['country'] == country].value_x.tolist()
        y_val = df_CO2_tot_to_forest[df_CO2_tot_to_forest['country'] == country].value_y.tolist()
        years = df_CO2_tot_to_forest[df_CO2_tot_to_forest['country'] == country].date.tolist()
        country_label = df_CO2_tot_to_forest[df_CO2_tot_to_forest['country'] == country].country.tolist()

        text = []
        for country, year in zip(country_label, years):
            text.append(str(country) + ' ' + str(year))

        graphs[2].append(go.Scatter(x = x_val, y = y_val, mode = 'lines+markers', text = text, name = country ) )

    layouts[2] = dict(title = 'CO2 emission VS forestal area',
                xaxis = dict(title = 'CO2 emission (kt)', rangemode = "nonnegative", type = "log"),
                yaxis = dict(title = 'Forestal area (sq. km)', rangemode = "nonnegative", type = "log"),)


    # fourth chart plots CO2 emissions over Forestal area for end_date as a bar chart

    # create a list of dictionaries with CO2 emission / forestal area
    CO2_over_for_list = []
    for country in countrylist:
        years_CO2 = df_CO2_tot[df_CO2_tot['country'] == country].date.tolist()
        years_for = df_forest[df_forest['country'] == country].date.tolist()
        years = [year for year in years_for if (year in years_CO2)]
        for year in years:
            new_row = {}
            new_row["country"] = country
            new_row["date"] = year
            CO2 = df_CO2_tot[(df_CO2_tot['country'] == country) & (df_CO2_tot['date'] == year)].value.tolist()
            for_area = df_forest[(df_forest['country'] == country) & (df_forest['date'] == year)].value.tolist()
            new_row["value"] = CO2[0]/for_area[0]
            CO2_over_for_list.append(new_row)

    df_CO2_tot_over_for = pd.DataFrame(CO2_over_for_list)
    # choose only data for end_date
    df_CO2_tot_over_for = df_CO2_tot_over_for[df_CO2_tot_over_for['date'] == str(end_date)]
    df_CO2_tot_over_for.sort_values('value', ascending=True, inplace=True)

    graphs[3].append( go.Bar(x = df_CO2_tot_over_for.country.tolist(), y = df_CO2_tot_over_for.value.tolist(),))

    layouts[3] = dict(title = 'CO2 emissions (kt) over Forestal area (sq. km) in ' + str(end_date),
                xaxis = dict(title = 'Country',),
                yaxis = dict(title = 'kt CO2 / km2 forestal area'), )



    # fifth chart plots renewable energy consumption from st_date to end_date in chosen economies
    # as a line chart

    # filtering plots the countries in decreasing order by their values
    df_renewable.sort_values('date', ascending=True, inplace=True)

    for country in countrylist:
        x_val = df_renewable[df_renewable['country'] == country].date.tolist()
        y_val =  df_renewable[df_renewable['country'] == country].value.tolist()
        graphs[4].append(go.Scatter(x = x_val, y = y_val, mode = 'lines', name = country))

    layouts[4] = dict(title = 'Renewable energy consumption',
                xaxis = dict(title = 'Year'),
                yaxis = dict(title = '% of total final energy consumption'),
                )

    # sixth chart plots renewable energy consumption for end_date as a bar chart
    df_renewable.sort_values('value', ascending=False, inplace=True)
    df_renewable = df_renewable[df_renewable['date'] == str(end_date)]

    graphs[5].append( go.Bar( x = df_renewable.country.tolist(), y = df_renewable.value.tolist(), ) )

    layouts[5] = dict(title = 'Renewable energy consumption in ' + str(end_date),
                    xaxis = dict(title = 'Country',),
                    yaxis = dict(title = '% of total final energy consumption'), )


    # seventh chart plots natural resources rent from st_date to end_date

    # filtering plots the countries in decreasing order by their values
    df_resources_rent.sort_values('date', ascending=True, inplace=True)

    for country in countrylist:
        x_val = df_resources_rent[df_resources_rent['country'] == country].date.tolist()
        y_val = df_resources_rent[df_resources_rent['country'] == country].value.tolist()
        graphs[6].append(go.Scatter(x = x_val, y = y_val, mode = 'lines', name = country))

    layouts[6] = dict(title = 'Total natural resources rents',
                xaxis = dict(title = 'Year'),
                yaxis = dict(title = '% of GDP'), )

    # eight chart plots natural resources rent for end_date as a bar chart
    df_resources_rent.sort_values('value', ascending=True, inplace=True)
    df_resources_rent = df_resources_rent[df_resources_rent['date'] == str(end_date)]

    graphs[7].append( go.Bar(x = df_resources_rent.country.tolist(), y = df_resources_rent.value.tolist(),))

    layouts[7] = dict(title = 'Total natural resources rents in ' + str(end_date),
                xaxis = dict(title = 'Country',),
                yaxis = dict(title = '% of GDP'),)


    # append all charts
    figures = []
    for i in range(len(graphs)):
        figures.append(dict(data=graphs[i], layout=layouts[i]))

    return figures
