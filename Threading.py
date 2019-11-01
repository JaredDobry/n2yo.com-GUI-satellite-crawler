#Data structure is defined as:
#2d array containing multiple sets of: [Associated category name, another array]
#where that array is defined as:
#1d array containing: [Satellite name, TLE line 1, TLE line 2, status message]

#Extra data for passing into worker threads is defined as:
#1d array containing: [APIKey, Category name, Satellite URL]
#The queue object that all threads will write results to (.puts() in an entry of the data structure defined above)

#Extra data for passing into the thread manager is defined as:
#2d array containing multiple sets of: [Category name, another array]
#where that array is defined as:
#1d array containing all of the urls for every satellite to scrape in the category

import threading
import queue
import requests
import tkinter as tk

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

#Scrapes a satellite from a url or the json query if an api key is present
def scrapeSatellite(apikey, url):
    if not "NONE" in apikey:
        #parse our url into the json request url
        try:
            ind = url.index("satellite/?s=")
            jsonURL = url[:ind]
            jsonURL += "rest/v1/satellite/tle/"
            jsonURL += url[ind + 13:] #append the satellite NORAD id
            jsonURL += "&apiKey=" + apikey
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
                out.append(tle[:ind])
                out.append(tle[ind + 2:])
                out.append("Found satellite: " + name + " (Transaction count: " + str(transactionCount) + ")")
                return out
            except ValueError:
                out.append("")
                out.append("")
                out.append("[ERROR] Could not parse TLE for satellite " + name)
                return out
        except ValueError:
            sys.exit("[ERROR] Could not parse satellite url: " + url + " for JSON query")
    else:
        r = requests.get(url)
        allText = r.text
        array = putStringIntoArray(allText)
        it = 0
        out = []
        for line in array:
            if it == 3:
                break
            elif "satname" in line:
                out.append(verifySatelliteName(parseHTMLValue(line)))
            elif "<pre>" in line:
                it += 1
            elif it == 1 or it == 2:
                out.append(line)
                it += 1
        out.append("Found " + out[0])
        return out
        
#finds all satellite urls in that category given the url
def scrapeCategory(url):
    r = requests.get(url)
    allText = r.text
    array = putStringIntoArray(allText)
    foundTable = False
    data = []
    for line in array:
        if "footable table" in line:
            foundTable = True
        elif foundTable == True:
            if "</table>" in line:
                return data
            elif "/satellite/?s=" in line:
                satExtension = parseHTMLSatLink(line)
                data.append(appendURL(url, satExtension))

#worker that does the request and pulls down the information
class WorkerThread(threading.Thread):
    def __init__(self, q, extra):
        threading.Thread.__init__(self)
        self.q = q
        self.e = extra
    def run(self):
        results = scrapeSatellite(self.e[0], self.e[2])
        self.q.put([self.e[1], results])
        return

class ThreadManager(threading.Thread):
    def __init__(self, q, extra, apikey):
        threading.Thread.__init__(self)
        self.q = q
        self.e = extra
        self.a = apikey
    def run(self):
        threads = []
        #Loop over every category
        for pair in self.e:
            #Loop over every satellite in the category
            if isinstance(pair[1], str):
                threads.append(WorkerThread(self.q, [self.a, pair[0], pair[1]]))
            else:
                for sat in pair[1]:
                    threads.append(WorkerThread(self.q, [self.a, pair[0], sat]))
        
        #Start all threads
        for t in threads:
            t.start()
            
        #Join all threads
        for t in threads:
            t.join()  
            
        return
        
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.data = {
            "url" : "",
            "apikey" : "",
            "scrapeTable" : [],
            "writeTable" : []
            }
        self.data["apikey"] = "NONE"
        #apikey = "GYGBEH-KN73X7-HDZEPD-47ZP"
        self._frame = None
        self.switchFrame(SatelliteDisplay)
        
    def switchFrame(self, frameClass):
        newFrame = frameClass(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = newFrame
        self._frame.pack()
        self._frame.run()

def UpdateText(frame, text):
    frame.text.config(state="normal")
    frame.text.insert("end", text + "\n")
    frame.text.config(state="disabled")
    frame.text.yview_moveto(1.0)

def SetupDisplay(frame):
    frame.text = tk.Text(frame)
    frame.text.pack(side="top", fill="both")
    frame.text.config(state="disabled")

def SetupDisplayWithScroll(frame):
    frame.scroll = tk.Scrollbar(frame)
    frame.scroll.pack(side="right", fill="y")
    frame.text = tk.Text(frame, yscrollcommand=frame.scroll.set)
    frame.text.pack(side="left", fill="both")
    frame.text.config(state="disabled")
    frame.scroll.config(command=frame.text.yview)

def StartThreadManager(frame):
    frame.q = queue.Queue() 
    #start scraper thread
    frame.threadmanager = ThreadManager(frame.q, frame.master.data["scrapeTable"], frame.master.data["apikey"])
    frame.threadmanager.start()   
    #update gui
    frame.after(16, frame.updater()) #roughly 60 fps   
        
class SatelliteDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)

        #set up UI
        SetupDisplay(self)

    def run(self):
        self.master.data["url"] = "https://www.n2yo.com/satellite/?s=44550"
        self.master.data["scrapeTable"].append(["NONE", self.master.data["url"]])
        StartThreadManager(self)

    def updater(self):
        try:
            item = self.q.get(False)
            if item is not None:
                UpdateText(self, "Satellite name: " + item[1][0] + "\nTLE:\n" + item[1][1] + "\n" + item[1][2] + "\n")
            self.after(16, self.updater)
        except queue.Empty:
            if self.threadmanager.is_alive():
                self.after(16, self.updater)
            else:
                UpdateText(self, "Complete")
                return

class SatelliteListDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)

class CategoryDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)

        
class CategoryListDisplay(tk.Frame):
    def __init__(self, master):  
        tk.Frame.__init__(self, master)

        #Set up UI elements
        SetupDiSetupDisplayWithScroll(self)
    
    def run(self):
        #Gather our starting info
        catlist = []
        catlist.append(["GlobalStar", scrapeCategory("https://www.n2yo.com/satellites/?c=17")])
        catlist.append(["Iridium", scrapeCategory("https://www.n2yo.com/satellites/?c=15")])

        self.master.data["scrapeTable"] = catlist       
        StartThreadManager(self)
        
    def updater(self):
        try:
            item = self.q.get(False)
            if item is not None:
                UpdateText(self, "Status: " + item[1][3])
            self.after(16, self.updater)
        except queue.Empty:
            if self.threadmanager.is_alive():
                self.after(16, self.updater)
            else:
                UpdateText(self, "Complete")
                return
        
app = App()
app.mainloop()