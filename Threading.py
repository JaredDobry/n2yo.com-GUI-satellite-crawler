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
        for category in self.e:
            #Loop over every satellite in the category
            for satellite in category[1]:
                threads.append(WorkerThread(self.q, [self.a, category[0], satellite]))
        
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
        self._frame = None
        self.switchFrame(ShowOutput)
        
    def switchFrame(self, frameClass):
        newFrame = frameClass(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = newFrame
        self._frame.pack()
        self._frame.run()
        
class ShowOutput(tk.Frame):
    def __init__(self, master):  
        tk.Frame.__init__(self, master)

        #Set up UI elements
        self.scroll = tk.Scrollbar(self)
        self.scroll.pack(side="right", fill="y")
        self.text = tk.Text(self, yscrollcommand=self.scroll.set)
        self.text.pack(side="left", fill="both")
        self.text.config(state="disabled")
        self.scroll.config(command=self.text.yview)
    
    def run(self):
        apikey = "NONE"
        #apikey = "GYGBEH-KN73X7-HDZEPD-47ZP"
        #Gather our starting info
        catlist = []
        catlist.append(["GlobalStar", scrapeCategory("https://www.n2yo.com/satellites/?c=17")])
        catlist.append(["Iridium", scrapeCategory("https://www.n2yo.com/satellites/?c=15")])
        
        self.q = queue.Queue() 
        #start scraper thread
        self.threadmanager = ThreadManager(self.q, catlist, apikey)
        self.threadmanager.start()   
        #update gui
        self.after(16, self.updater()) #roughly 60 fps   
        
    def updater(self):
        try:
            item = self.q.get(False)
            if item is not None:
                self.updateText("Status: " + item[1][3])
            self.after(16, self.updater)
        except queue.Empty:
            if self.threadmanager.is_alive():
                self.after(16, self.updater)
            else:
                self.updateText("Complete")
                return
    
    def updateText(self, text):
        self.text.config(state="normal")
        self.text.insert("end", text + "\n")
        self.text.config(state="disabled")
        self.text.yview_moveto(1.0)
        
app = App()
app.mainloop()