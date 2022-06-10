# Firestar-burner-log_webscrape

This is a small script I wrote to 'webscrape' a text table from an HTML website displaying the daily log for my family's Firestar wood gasifying furnace.  I use it to store a local record of how the boiler is performing.

Make sure to update the operating directory for where the script should search for the log file to update.  Also, update the USERNAME and BOILERID within the script.  You can find these by logging into the website to view your own burner's performance.

It can be run from the terminal using the shell- ie `$ python Scrape-Firestar-BurnerChart_standalone_2019-03-04.py` and will prompt for your password... Use the --help flag to see additional details for use.
