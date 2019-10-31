~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Created by Jared Dobry
Field questions to jared.m.dobry.ctr@mail.mil
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Requirements for use:
	1. An internet connection that is allowed to access outside web domains (DON'T run this on a class computer!)
		Note: If you need this data on a classified computer, generate the files on an unclassified workspace and go through the necessary channels to move the data over
	2. Python 3.x.x
	3. Package "requests"
		If you do not have requests already, here is how to install it:
		1. Open the command line
		2. Attempt to run: python -m pip install requests
			If this works, you have requests installed and can run the script now
		3. If 2. didn't work, then try: python -m pip install --user requests
			This will install requests locally for THIS USER ONLY, it must be repeated for any user who wishes to use the script!
		4. If 3. didn't work, cry! (ask a sysadmin to install the package for you)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NOTE: The best way to use the crawler/creator scripts is locally in a command shell, so you can see error messages!
All files will be generated locally, and all config files must exist locally in the directory of the scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
API Key usage for the crawler:
If you register with n2yo.com, you can generate an API key so that we can access their JSON api query.
The benefits to using the API key is slightly faster data transfer, so you can get all of your satellites downloaded faster.
There is a drawback however, you are limited to 1000 transactions with the JSON api per hour. If you need more than that, you might want to try to scrape from the website without the API key.
They may blacklist your IP address if you're regularly asking for more than 1000 transactions an hour via scraping, so I would be weary about doing that.

If you decide to use an API key, place it into APIKey.txt, with no extra characters.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Documentation for use (CRAWLER):
The satellite crawler is used to scrape TLE data off of n2yo.com's free database of unclassified satellite data
The scraper can do the following:
	1. Pull an individual satellite's TLE data
	2. Pull a list of satellites TLE data into a file that you specify
	3. Pull an entire category of satellites TLE data into a file named after that category
	4. Pull a list of categories TLE data into individual files for each category

Syntax for use case:
	1. Just input the satellites URL, that's it
	2. In SatelliteList.txt, input each satellites URL followed by an enter key (\n character)
	   The scraper will prompt you at the end of it's data gathering for a filename to save to.
	   Note: you need to input the filename as well as the extension. eg: file.txt
	3. The scraper will prompt you for a category name eg: Iridium and the url of the category, eg: https://www.n2yo.com/satellites/?c=15
	   The scraper will pull down all of the data for each satellite in that category, and will save it to a file named after you category, eg: IridiumSatellites.txt
	4. In CategoriesList.txt, each line must be constructed like so:
	   CategoryName=Brightest URL=https://www.n2yo.com/satellites/?c=1
	   There should be no spaces between the = signs, and only 1 space following the end of the category name.
	   The url should be followed by a return key (\n character) and nothing else
	   The scraper will save each categories list of satellite TLE data to an individual file named after each category, eg: IridiumSatellites.txt, BrightestSatellites.txt, etc

Where do these files go?
	The .txt file holds the TLE data, and must be placed somewhere in the database that you are using.
	As an example, the convention for putting this data in for UNCLASSIFIED would be to place it in UNCLASSIFIED\model\Contact
	
How often should I use this tool?
	TLE data is imprecise and decays fairly rapidly. A good rule of thumb is to re-download all TLE data about every week to 2 weeks.
	(Remember to go put it in the data directory again!)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~	   
Documentation for use (CREATOR):
The satellite creator is used to generate player template files for use in NGTS. 
It requires that you have already used the crawler to download the TLE data, and have specified where this data is in WriterConfig.txt
To specify which satellites to generate, enter in each .txt file that has satellite TLE data in it. 
The generator goes off of the filename to determine what category to place the satellites in, so IridiumSatellites.txt will get placed in the 'Iridium' category on battlemonitor
The creator can do the following:
	1. Create a player template for every satellite inside of the .txt files specified in WriterConfig.txt
	2. Create a player group template that has every single satellite available to drop all at once
		Note: The player group templates won't work unless you generate player templates!

Syntax for use:
	1. Ensure that WriterConfig.txt has the list of all files you want to generate templates for.
	   These should be in the format of: FileName.txt + a return character (\n character)
	2. Decide whether to generate player templates, group templates, or both (you will be prompted)

Where do these files go?
	The .xml file holds the player templates, and must be placed in the player templates folder in your data directory.
	The convention would be to place them in UNCLASSIFIED\PlayerTemplates\Space
	The player group template .xml file is the reference to every player inside that player template file.
	The convention would be to place them in UNCLASSIFIED\PlayerTemplates\PlayerGroupTemplates
	
How often should I use this tool?
	You don't need to generate the player templates and group templates more than once, unless you are editing the list of satellites in that grouping/category
	Verify that your TLE data is up to date, you only need to regenerate the templates if you have changed the filename of the .txt file that is used for generation
	(Remember to go put it in the data directory again!)