#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar  4 12:33:39 2019

This is a script to extract data about my family's wood burner and it's usage.  It imports data from a file with
all previous burner data, as well as webscrapes new data for the previous day for each run, and puts them together
and prints to a new file.  It does this on a monthly basis (when month changes, it starts a new file).

To get weather data for previous days: https://www.wunderground.com/personal-weather-station/dashboard?ID=KWIPOPLA9#history/tdata/s20190316/e20190316/mdaily
This is for Poplar, WI.  And all that needs to be changed is the date integers above- i.e. 20190316

Another potential tool: https://pypi.org/project/WunderWeather/

@author: danlevings
"""

# Import libraries
import sys
import argparse
import socket
import errno
import os
import platform
import datetime
import re
import getpass
import pandas
import xlsxwriter
import requests
from bs4 import BeautifulSoup
from collections.abc import Iterable

def parse_args(): 
    '''
    Gives options
    '''
    parser = argparse.ArgumentParser(description="Retrieves woodburner log and updates Excel file in Dropbox.  Required argument is password.  Date is optional (if none provided, yesterday's date will be used).")
    parser.add_argument('--date', help='Provide custom date to retrieve in format [YYYY-MM-DD].')
    parser.add_argument('--customdate', help='Input "yes" if you want to use a custom date, or else yesterday will be used.')
    args = parser.parse_args()
    url_date = str(args.date)
    url_true = str(args.customdate)
    
    return url_date, url_true

def main():
    try:
        '''
        Runs the actual process of retreiving the FireStar data
        '''

        url_date, url_true = parse_args()

        # Read in file
        password = getpass.getpass("Please provide password for My FireStar:  ")
        password = str(password)
        password = password.rstrip()

        # Code to setup the pertinent string "prefix" for assigning/changing directories - change this to appropriate directory
        origin_folder = "/home/daniel/Desktop/"
        
        # Now switch to Dropbox directory for storing this data
        # change working directory and check
        os.chdir(origin_folder)
        # os.getcwd()
        
        ## Now import previous Firestar data
        # First grab the filenames and dates corresponding to any relevant previous logs
        all_files = os.listdir(origin_folder)
        firestar_regex = re.compile(r'^(FireStar-WoodBurner-Log_([0-9\-]{6,7})\.xlsx?)$', flags=re.IGNORECASE)
        firestar_files = []
        firestar_files_dates = []
        for item in range(0,len(all_files)):
            try:
                firestar_files.append(re.search(firestar_regex,all_files[item]).group(1))
                firestar_files_dates.append(re.search(firestar_regex,all_files[item]).group(2))
            except:
                pass
        del item
        firestar_files_dates.sort(reverse=True)
        
        # Split into month and year
        firestar_date_regex = re.compile(r'^([0-9]{4})\-?([0-9]{1,2})$', flags=re.IGNORECASE)
        firestar_year = []
        firestar_month = []
        firestar_year.append(re.search(firestar_date_regex, firestar_files_dates[0]).group(1))
        firestar_month.append(re.search(firestar_date_regex, firestar_files_dates[0]).group(2))
        firestar_year = int(firestar_year[0])
        firestar_month = int(firestar_month[0])
        
        # Next get the current date
        current_date = str(datetime.datetime.today())
        date_regex = re.compile(r'^([0-9]{4})\-([0-9]{1,2})\-([0-9]{1,2})\ ?[0-9]+\:[0-9]+:[0-9\.]+$', flags=re.IGNORECASE)
        current_year = []
        current_day = []
        current_month = []
        current_year.append(re.search(date_regex, current_date).group(1))
        current_day.append(re.search(date_regex, current_date).group(3))
        current_month.append(re.search(date_regex, current_date).group(2))
        current_year = int(current_year[0])
        current_day = int(current_day[0])
        current_month = int(current_month[0])
        
        # Retrieve file corresponding to most recent date
        most_recent_regex = ["^.*", str(firestar_files_dates[0]), ".xlsx?$"]
        most_recent_regex = ''.join(most_recent_regex)
        most_recent_regex = re.compile(most_recent_regex, flags=re.IGNORECASE)
        most_recent_file = filter(most_recent_regex.match, firestar_files)
        most_recent_file = ''.join(most_recent_file)
        
        # Now, if the current date is the same month as the previous date, load in old file
        # If it is a new month (and the second day) make a new file
        if (current_month == firestar_month) and (current_year == firestar_year):
            old_table = pandas.read_excel(io = most_recent_file, header = 0, index_col = None)
        elif (current_month == firestar_month + 1) and (current_year == firestar_year) and (current_day == 1):
            old_table = pandas.read_excel(io = most_recent_file, header = 0, index_col = None)
        else:
            old_table = pandas.DataFrame(columns = ['Timestamp', 'Status', 'Mode', 
                                    'Fan', 'Water Temp', 'Reaction Chamber Temp', 'Primary Air', 
                                    'Sec. Air', 'Burn Time', 'Alarms'])
        
        # Make sure the old table has the same format as the new
        old_table.columns = ['Timestamp', 'Status', 'Mode', 
                                    'Fan', 'Water Temp', 'Reaction Chamber Temp', 'Primary Air', 
                                    'Sec. Air', 'Burn Time', 'Alarms']
        old_table = old_table.fillna('')
        
        # Specify URL for loggin into My Firestar logon page
        login_url = "https://myfirestar.com/Account/LogOn"
        
        # Logon credentials - make sure to replace <USERNAME> with yours
        form_data = {"UserName": "<USERNAME>", "Password": password} 
        
        # Pass URL info for specific date
        if (str(url_true) == "yes"): 
            pass
        else:
            if (len(str(current_month)) < 2):
                current_month_tmp = str("0" + str(current_month))
            else:
                current_month_tmp = str(current_month)
            if (len(str(current_day)) < 2):
                current_day_tmp = str("0" + str(current_day - 1))
            else:
                current_day_tmp = str(current_day - 1)
            url_date = str(current_year) + "-" + str(current_month_tmp) + "-" + str(current_day_tmp)
            del current_month_tmp, current_day_tmp
        
        # Specify page for data  --  also change <BOILERID> to your own burner ID
        internal_url = "https://www.myfirestar.com/Home/Chart/<BOILERID>?StartDate=" + url_date + "&SpanSize=24&SpanIndex=0&tempUnits=f"
        
        # Extract data from specified page
        with requests.Session() as sesh:
            sesh.post(login_url, data=form_data)
            response = sesh.get(internal_url)
            html = response.text
        
        # Convert to BeautifulSoup4 object for parsing
        soup = BeautifulSoup(html, 'lxml')
        
        # To see/print whole webpage
        # soup.prettify()
        
        # Extract the data table only from page
        data_table = list(soup.children)[4]
        
        # Initiate table for data
        firestar_table = pandas.DataFrame(columns=range(0,10))
        
        # Initiate row for extracting data (skip row 1, which is the header)
        row_marker=1
        
        # Extract all table data into Pandas DataFrame
        for row in data_table.find_all('tr'):
                column_marker = 0
                columns = row.find_all('td')
                for column in columns:
                    firestar_table.at[row_marker,column_marker] = column.get_text()
                    column_marker += 1
                row_marker += 1
        
        # Then rename columns
        firestar_table.columns = ['Timestamp', 'Status', 'Mode', 
                                    'Fan', 'Water Temp', 'Reaction Chamber Temp', 'Primary Air', 
                                    'Sec. Air', 'Burn Time', 'Alarms']
        
        # Strip newlines from Alarms column
        firestar_table['Alarms'] = firestar_table['Alarms'].str.replace("\n",'')
        
        # Strip newlines and Celcius values from Temp columns
        firestar_table['Water Temp'] = firestar_table['Water Temp'].str.replace("\n[0-9\.]+.{1}C\n",'')
        firestar_table['Water Temp'] = firestar_table['Water Temp'].str.replace("\n",'')
        firestar_table['Reaction Chamber Temp'] = firestar_table['Reaction Chamber Temp'].str.replace("\n[0-9\.]+.{1}C\n",'')
        firestar_table['Reaction Chamber Temp'] = firestar_table['Reaction Chamber Temp'].str.replace("\n",'')
        
        # Create function to change percent values to float
        def percent2float(x):
            return float(x.strip('%'))/100
        
        # Use on air values
        firestar_table = firestar_table.reindex()
        for item in range(0,len(firestar_table)):
            firestar_table.iloc[item]['Primary Air'] = percent2float(firestar_table.iloc[item]['Primary Air'])
            firestar_table.iloc[item]['Sec. Air'] = percent2float(firestar_table.iloc[item]['Sec. Air'])
        del item
        
        # 'remove' NA's
        firestar_table = firestar_table.fillna('')
        
        # Now concatenate the new data Pandas dataframe with the old
        full_df = pandas.concat(objs = [old_table, firestar_table], axis=0)
        full_df = full_df.drop_duplicates()
        
        # Make new function for flattening list of list of strings
        def flatten(coll):
            for i in coll:
                    if isinstance(i, Iterable) and not isinstance(i, str):
                        for subc in flatten(i):
                            yield subc
                    else:
                        yield i
        
        # Extract timestamps, and change to 24 hour time
        timestamps = []
        for item in range(0, len(full_df)):
            timestamp_split = full_df.iloc[item]['Timestamp'].split(':')
            all_split = []
            for i in timestamp_split:
                i_split = i.split(' ')
                tmp = flatten(i_split)
                tmp = list(tmp)
                all_split = [all_split, tmp]
            all_split = flatten(all_split)
            all_split = list(all_split)
            all_split = [all_split[0].split('/'), all_split[1],  all_split[2],  all_split[3],  all_split[4]]
            all_split = flatten(all_split)
            all_split = list(all_split)
            if (str(all_split[6]) == 'PM') and (int(all_split[3]) != 12):
                all_split[3] = str(int(all_split[3])+12)
            elif (str(all_split[6]) == 'AM') and (int(all_split[3]) == 12):
                all_split[3] = str("00")
            elif (str(all_split[6]) == 'AM') and (len(str(all_split[3])) < 2) and (int(all_split[3]) != 12):
                all_split[3] = str("0"+ all_split[3])
            else:
                pass
            if (len(str(all_split[1])) < 2):
                all_split[1] = str("0"+ all_split[1])
            else:
                pass
            timestamps.append(
                str(all_split[0] + " " + all_split[1] + " " + all_split[2] + 
                    " " + all_split[3] + "-" + all_split[4] + "-" + all_split[5]))
        del item, all_split, i, i_split, tmp, timestamp_split
        timestamps = list(flatten(timestamps))
        
        # Now convert this to a dataframe and sort according to time
        timestamps = pandas.DataFrame(data = timestamps, columns = ['Timestamp'])
        timestamps = timestamps['Timestamp'].str.split(" ", n = 4, expand = True)
        timestamps.columns = ['Month', 'Day', 'Year', 'Time']
        
        # Sort full df by the sorted index of the dataframe above
        timestamps.reset_index(drop=True, inplace=True)
        full_df.reset_index(drop=True, inplace = True)
        full_df = pandas.concat(objs = [full_df, timestamps], axis=1)
        full_df.sort_values(by=['Day','Time'], ascending=[False,False], inplace=True)
        
        # Reset index and remove those added columns
        full_df.reset_index(drop=True, inplace = True)
        full_df.drop(labels = ['Month', 'Day', 'Year', 'Time'], axis=1, inplace=True)
        
        # create metadata for file
        from datetime import date
        create_date = "{:%Y-%m}".format(date.today())
        filename = ['FireStar-WoodBurner-Log_',
                    create_date,
                    '.xlsx']
        
        # write to file
        writer = pandas.ExcelWriter(''.join(filename), engine='xlsxwriter')
        full_df.to_excel(excel_writer=writer, index=False)
        writer.save()
    except socket.error as e:
        if e.errno != errno.EPIPE:
                # Not a broken pipe
                raise
        sys.exit(1)  # Python exits with error code 1 on EPIPE

if __name__ == '__main__':
    main()
