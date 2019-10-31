import requests
import sys

#removes illegal characters ' and & from satellite names
def verifySatelliteName(name):
    try:
        result = name.index("'")
        newStr = name[:result] + name[result + 1:]
        return verifySatelliteName(newStr)
    except ValueError:
        try:
            result = name.index("&")
            newStr = name[:result] + name[result + 1:]
            return verifySatelliteName(newStr)
        except ValueError:
            return name

#scrapes out the HTML "value" tag
def parseHTMLValue(input):
    try:
        result = input.index("value=")
        tempStr = input[result + 7:-2]
        return tempStr
    except ValueError:
        print("[ERROR] Could not find 'value=' in string:\n")
        print(input)
        return "error"

#scrapes out the extension for the satellites URL
def parseHTMLSatLink(input):
    try:
        result = input.index("/satellite/?s=")
        tempStr = input[result:result + 19]
        try:
            result = tempStr.index("\"")
            return tempStr[:result]
        except ValueError:
            return tempStr
    except ValueError:
        print("[ERROR] Could not find '/satellite/?s=' in string:\n")
        print(input)
        return "error"
       
#appends the new extension onto the parent url
def appendURL(url, extension):
    try:
        result = url.index("satellites")
        tempStr = url[0:result]
        tempStr += extension
        return tempStr
    except ValueError:
        print("[ERROR] Could not parse 'satellites' in master url:\n")
        print(url)
        return ("error")

#takes a giant raw HTML string and formats it into a line array
def putStringIntoArray(string):
    array = []
    line = ""
    for char in string:
        if char == '\n':
            array.append(line)
            line = ""
        elif char != '\r':
            line += char
    array.append(line)
    return array

#scrapes the name and TLE from a single satellite given it's url
def scrapeSatellite(url, useAPI):
    if useAPI == 0:
        #parse our url into the json request url
        try:
            fr = open("APIKey.txt", "r")
            apiKey = fr.readline()
            fr.close()
            try:
                ind = url.index("satellite/?s=")
                jsonURL = url[:ind]
                jsonURL += "rest/v1/satellite/tle/"
                jsonURL += url[ind + 13:] #append the satellite NORAD id
                jsonURL += "&apiKey=" + apiKey
                r = requests.get(jsonURL)
                js = r.json()
                out = []
                info = js["info"]
                name = verifySatelliteName(info["satname"])
                transactionCount = info["transactionscount"]
                out.append(name)
                tle = js["tle"]
                #parse the lines
                try:
                    ind = tle.index("\r\n")
                    print("Found satellite: " + name + " (Transaction count: " + str(transactionCount) + ")")
                    out.append(tle[:ind])
                    out.append(tle[ind + 2:])
                    return out
                except ValueError:
                    print("[ERROR] Could not parse TLE for satellite " + name)
                    out.append("")
                    out.append("")
                    return out
            except ValueError:
                sys.exit("[ERROR] Could not parse satellite url: " + url + " for JSON query")
        except IOError:
            sys.ext("[ERROR] Could not open APIKey.txt for reading")
    else:
        r = requests.get(url)
        allText = r.text
        array = putStringIntoArray(allText)
        line1 = True
        line2 = False
        name = ""
        l1 = ""
        l2 = ""
        for line in array:
            if "<pre>" in line:
                line1 = True
            elif line1 == True:
                l1 = line
                line1 = False
                line2 = True
            elif line2 == True:
                l2 = line
                line2 = False
            elif "satname" in line:
                name = verifySatelliteName(parseHTMLValue(line))
                print("Found satellite: " + name)
        return [name, l1, l2]
    
#scrapes an entire category given the categories url
def scrapeCategory(url, useAPI):
    dataVector = []
    r = requests.get(url)
    allText = r.text
    array = putStringIntoArray(allText)
    foundTable = False
    for line in array:
        if "footable table" in line:
            foundTable = True
        if foundTable == True:
            if "</table>" in line:
                return dataVector
            elif "/satellite/?s=" in line:
                satExtension = parseHTMLSatLink(line)
                satURL = appendURL(url, satExtension)
                dataVector.append(scrapeSatellite(satURL, useAPI))

#Determines user input                
def determineSelection():
    print("Do you want to scrape:\n")
    print("[0] A single satellite\n")
    print("[1] A list of satellites\n")
    print("[2] An entire category of satellites\n")
    print("[3] A list of categories of satellites\n")
    selection = input()
    if '0' in selection:
        return 0
    elif '1' in selection:
        return 1
    elif '2' in selection:
        return 2
    elif '3' in selection:
        return 3
    else:
        print("\n[ERROR] Invalid selection\n")
        return determineSelection()

#Determines whether to use an API key or not
def determineAPIKey():
    print("Use the API key?")
    print("[Y] or [N]")
    selection = input()
    if selection == 'y' or selection == 'Y':
        return 0
    elif selection == 'n' or selection == 'N':
        return 1
    else:
        print("[ERROR] Please input Y or N")
        return determineAPIKey()

#Writes a list of satellites to a filename given by the user        
def writeSatelliteListToFile(filename, data):
    try:
        f = open(filename, "w")
        for array in data:
            if array[1] == "":
                print("[ERROR] Satellite " + array[0] + " has no TLE data, ignoring")
                continue
            for entry in array:
                f.write(entry + "\n")
        f.close()
    except IOError:
        errStr = "[ERROR] Problem opening " + filename + " for writing, terminating"
        sys.exit(errStr)

#Writes a category of satellites to a file        
def writeCategoryToFile(cat, data):
    filename = cat + "Satellites.txt"
    print("Writing category: " + cat + " to file: " + filename)
    writeSatelliteListToFile(filename, data)

#parses the category name and url out of our CategoriesList.txt
def parseCategoryLine(line):
    try:
        catIndex = line.index("CategoryName=")
        urlIndex = line.index("URL=")
        category = line[catIndex + 13: urlIndex - 1]
        url = line[urlIndex + 4:]
        return [category, url]
    except ValueError:
        errStr = "Could not parse category line: " + line
        sys.exit(errStr)
    
#Begin main function
useAPI = determineAPIKey()
selection = determineSelection()
if selection == 0:
    print("Please input satellite url (from n2yo.com):\n")
    temp = input()
    print(scrapeSatellite(temp, useAPI))
elif selection == 1:
    print("Attempting to read SatelliteList.txt")
    try:
        f = open("SatelliteList.txt", "r")
        lines = f.readlines()
        data = []
        for line in lines:
            if "\n" in line:
                ind = line.index("\n")
                data.append(scrapeSatellite(line[0:ind], useAPI))
            else:
                data.append(scrapeSatellite(line, useAPI))
        print("Filename to save to:\n")
        filename = input()
        writeSatelliteListToFile(filename, data)
    except IOError:
        sys.exit("[ERROR] Problem opening SatelliteList.txt, verify the file exists in the same directory as this script")
elif selection == 2:
    print("Please input the name of the category:\n")
    cat = input()
    print("Please input category url (from n2yo.com):\n")
    temp = input()
    data = scrapeCategory(temp, useAPI)
    writeCategoryToFile(cat, data)
elif selection == 3:
    print("Attempting to read CategoriesList.txt")
    try:
        f = open("CategoriesList.txt", "r")
        lines = f.readlines()
        for line in lines:
            fixline = line
            if "\n" in line:
                ind = line.index("\n")
                fixline = line[0:ind]
            [category, url] = parseCategoryLine(fixline)
            print("\nAttempting to scrape category: " + category + "\n")
            data = scrapeCategory(url, useAPI)
            writeCategoryToFile(category, data)
    except IOError:
        sys.exit("[ERROR] Problem opening CategoriesList.txt")
else:
    sys.exit("[ERROR] Selection error should not have gotten this far, terminating")
    
