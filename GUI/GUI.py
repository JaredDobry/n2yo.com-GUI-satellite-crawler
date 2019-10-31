import tkinter as tk
import sys
import requests
import threading
import queue

def handleWrite(filename, data):
    file = filename
    try:
        ind = filename.index("\n")
        file = filename[:ind]
    except ValueError:
        file = filename
    try:
        fw = open(file, "w")
        for d in data:
            if d[1] == "":
                continue
            else:
                for entry in d:
                    fw.write(entry + "\n")
        fw.close()
        return "SUCCESS"
    except IOError:
        return "Couldn't Open " + file

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

#scrapes the name and TLE from a single satellite given it's url
def scrapeSatellite(url, APIKey):
    if not "NONE" in APIKey:
        #parse our url into the json request url
        try:
            ind = url.index("satellite/?s=")
            jsonURL = url[:ind]
            jsonURL += "rest/v1/satellite/tle/"
            jsonURL += url[ind + 13:] #append the satellite NORAD id
            jsonURL += "&apiKey=" + APIKey
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
        line1 = False
        line2 = False
        out = []
        for line in array:
            if "<pre>" in line:
                line1 = True
            elif line1 == True:
                out.append(line)
                line1 = False
                line2 = True
            elif line2 == True:
                out.append(line)
                line2 = False
            elif "satname" in line:
                out.append(verifySatelliteName(parseHTMLValue(line)))
        out.append("Found satellite: " + out[0])
        return out

class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self._frame = None
        self.sharedData = {
            "APIKey": tk.StringVar(),
            "Selection": tk.StringVar(),
            "SatelliteList": [],
            "CategoryList": [],
            "SatelliteData": [],
            "URL": ""
        }
        self.switchFrame(APIMenu)
        
    def switchFrame(self, frameClass):
        newFrame = frameClass(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = newFrame
        self._frame.pack()     
        
class APIMenu(tk.Frame):
    def __init__(self, master):   
        tk.Frame.__init__(self, master)
        self.master.geometry("500x410")
        self.master = master
        self.label = tk.Label(self, text="Would you like to use the API key?")
        self.label.pack(side="top")
        
        self.textEdit = tk.Text(self)
        self.textEdit.pack(side="top")
        self.textEdit.insert("end", self.readAPIKey())
        self.textEdit.config(height=1, width=33)
        self.bindID = self.master.bind('<Return>', self.handleReturn)
        
        tk.Button(self, command= self.handleYes, text="Yes", width=18).pack(side="left")
        tk.Button(self, command= self.handleNo, text="No", width=18).pack(side="right")
        
    def readAPIKey(self):
        try:
            fr = open("APIKey.txt", "r")
            key = fr.readline()
            fr.close()
            return key
        except IOError:
            return "Please enter API Key"
    
    def handleReturn(self, event):
        self.handleYes()
    
    def handleYes(self):
        contents = self.textEdit.get(1.0, "end")
        try:
            ind = contents.index("\n")
            contents = contents[:ind]
        except ValueError: ()
        if "Please enter API Key" not in contents and len(contents) == 25:
            self.master.sharedData["APIKey"].set(contents)
            try:
                fw = open("APIKey.txt", "w")
                fw.write(contents)
                fw.close()
            except IOError:
                print("Error encountered opening APIKey.txt for writing")
            self.master.unbind('<Return>', self.bindID)
            self.master.switchFrame(CrawlerSelectionMenu)
        else:
            self.label.config(text="Invalid API key")
            self.textEdit.delete(1.0, "end")
    
    def handleNo(self):
        self.master.sharedData["APIKey"].set("NONE")
        self.master.switchFrame(CrawlerSelectionMenu)

class CrawlerSelectionMenu(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.master = master
        tk.Label(self, text="Select a scraping option").pack()
        tk.Button(self, text="Single Satellite", command=self.handleSat).pack(fill="both")
        tk.Button(self, text="List of Satellites", command=self.handleSatList).pack(fill="both")
        tk.Button(self, text="Category of Satellites", command=self.handleCat).pack(fill="both")
        tk.Button(self, text="List of Categories", command=self.handleCatList).pack(fill="both")
        
    def handleSat(self):
        self.master.switchFrame(SatelliteCrawlerMenu)
    def handleSatList(self):
        self.master.switchFrame(SatelliteListCrawlerMenu)
    def handleCat(self):
        self.master.switchFrame(CategoryCrawlerMenu)
    def handleCatList(self):
        self.master.switchFrame(CategoryListCrawlerMenu)   
        
class SatelliteCrawlerMenu(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        
class SatelliteListCrawlerMenu(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        self.label = tk.Label(self, text="Satellite list filename:")
        self.label.grid(row = 0)
        self.text = tk.Text(self, height=1)
        self.text.insert("end", "SatelliteList.txt")
        self.bindID = self.master.bind('<Return>', self.handleReturn)
        self.text.grid(row = 0, column = 1)
        
    def handleReturn(self, event):
        contents = self.text.get(1.0, "end")
        try:
            ind = contents.index("\n")
            contents = contents[:ind]
        except ValueError:
            print("Filename fine")
        if not ".txt" in contents:
            self.label.config(text="Invalid file extension, input a .txt file:")
            self.text.delete(1.0, "end")
        else:
            try:
                fr = open(str(contents), "r")
                lines = fr.readlines()
                satList = []
                for line in lines:
                    if "\n" in line:
                        satList.append(line[:-1])
                    else:
                        satList.append(line)
                self.master.sharedData["SatelliteList"] = satList
                self.master.unbind('<Return>', self.bindID)
                self.master.switchFrame(ShowSatListCrawl)
            except IOError:
                self.label.config(text="Error opening file: " + str(contents))
                self.text.delete(1.0, "end")

class CategoryCrawlerMenu(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        self.label = tk.Label(self, text="Category URL:")
        self.label.grid(row = 0)
        self.text = tk.Text(self, height=1)
        self.bindID = self.master.bind('<Return>', self.handleReturn)
        self.text.grid(row = 0, column = 1)
        
    def handleReturn(self, event):
        contents = self.text.get(1.0, "end")
        try:
            ind = contents.index("\n")
            contents = contents[:ind]
        except ValueError: ()
        if not "?c=" in contents:
            self.label.config(text="Invalid URL, retry:")
            self.text.delete(1.0, "end")
        else:
            self.master.sharedData["URL"] = contents
            self.master.unbind("<Return>", self.bindID)
            self.master.switchFrame(ShowCatCrawl)

class CategoryListCrawlerMenu(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        self.label = tk.Label(self, text="Category list filename:")
        self.label.grid(row = 0)
        self.text = tk.Text(self, height=1)
        self.text.insert("end", "CategoryList.txt")
        self.bindID = self.master.bind('<Return>', self.handleReturn)
        self.text.grid(row = 0, column = 1)
        
    def handleReturn(self, event):
        contents = self.text.get(1.0, "end")
        try:
            ind = contents.index("\n")
            contents = contents[:ind]
        except ValueError:
            print("Filename fine")
        if not ".txt" in contents:
            self.label.config(text="Invalid file extension, input a .txt file:")
            self.text.delete(1.0, "end")
        else:
            try:
                fr = open(str(contents), "r")
                lines = fr.readlines()
                catList = []
                for line in lines:
                    editline = line
                    if "\n" in line:
                        editline = line[:-1]
                    try:
                        catIndex = line.index("CategoryName=")
                        urlIndex = line.index("URL=")
                        category = line[catIndex + 13: urlIndex - 1]
                        url = line[urlIndex + 4:]
                        catList.append([category, url])
                    except ValueError:
                        sys.exit("Error parsing category list file")
                self.master.sharedData["CategoryList"] = catList
                self.master.unbind('<Return>', self.bindID)
                self.master.switchFrame(ShowCatListCrawl)
            except IOError:
                self.label.config(text="Error opening file: " + str(contents))
                self.text.delete(1.0, "end")
        
class ShowSatCrawl(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
            
class SatListThread(threading.Thread):
    def __init__(self, queue, urls, apiKey):
        threading.Thread.__init__(self)
        self.queue = queue
        self.urls = urls
        self.apiKey = apiKey
    def run(self):
        threads = []
        for url in self.urls:
            threads.append(SatScraperThreadWorker(self.queue, url, self.apiKey))
        
        for t in threads:
            t.start()
        print("All threads started")
         
        for t in threads:
            t.join()
        print("All threads joined")
        
        sys.exit()
            
class CategoryThread(threading.Thread):
    def __init__(self, queue, url, apiKey):
        threading.Thread.__init__(self)
        self.queue = queue
        self.url = url
        self.apiKey = apiKey
    def run(self):
        r = requests.get(self.url)
        allText = r.text
        array = putStringIntoArray(allText)
        foundTable = False
        threads = []
        for line in array:
            if "footable table" in line:
                foundTable = True
            if foundTable == True:
                if "</table>" in line:
                    break
                elif "/satellite/?s=" in line:
                    satExtension = parseHTMLSatLink(line)
                    satURL = appendURL(self.url, satExtension)
                    newThread = SatScraperThreadWorker(self.queue, satURL, self.apiKey)
                    threads.append(newThread)
                    
        #Start all threads
        for t in threads:
            t.start()
        
        print("All threads started")
        
        #Join all threads
        for t in threads:
            t.join()
            
        print("All threads joined")
        sys.exit()
                    
class SatScraperThreadWorker(threading.Thread):
    def __init__(self, queue, url, apiKey):
        threading.Thread.__init__(self)
        self.queue = queue
        self.url = url
        self.apiKey = apiKey
    def run(self):
        data = scrapeSatellite(self.url, self.apiKey)
        self.queue.put(data, True, None)
        sys.exit()

class ShowSatListCrawl(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        self.master.geometry("500x410")
        
        topFrame = tk.Frame(self)
        topFrame.pack(side="top", fill="both")
        self.scroll = tk.Scrollbar(topFrame)
        self.scroll.pack(side="right", fill="y")
        self.text = tk.Text(topFrame, yscrollcommand=self.scroll.set)
        self.text.pack(side="left", fill="both")
        self.scroll.config(command=self.text.yview)
        self.queue = queue.Queue()
        self.scrapeThread = SatListThread(self.queue, self.master.sharedData["SatelliteList"], self.master.sharedData["APIKey"].get())
        self.scrapeThread.start() 
        self.updater()
    
    def updater(self):   
        if self.scrapeThread.is_alive():
            item = self.queue.get()
            if item is None:
                self.after(10, self.updater)
            else:
                self.updateText(item)
                self.after(10, self.updater)
        else:
            if not self.queue.empty():
                item = self.queue.get()
                if item is not None:
                    self.updateText(item)
                    self.after(10, self.updater)
            else:        
                self.text.config(state="normal")
                self.text.insert("end", "All workers done, save your data!\n")
                self.text.config(state="disabled")
                self.text.yview_moveto(1.0)
                
                bottomFrame = tk.Frame(self)
                bottomFrame.pack(side="bottom")
                self.saveLabel = tk.Label(bottomFrame, text="Save to file: ")
                self.saveLabel.pack(side="left")  
                self.saveText = tk.Text(bottomFrame, height = 1)
                self.saveText.pack(side="right")
                self.bindID = self.master.bind("<Return>", self.handleReturn)                    
                return
    
    def updateText(self, item):
        self.master.sharedData["SatelliteData"].append(item[:-1])
        self.text.config(state="normal")
        self.text.insert("end", item[3] + "\n")
        self.text.config(state="disabled")
        self.text.yview_moveto(1.0)
    
    def handleReturn(self, event):
        result = handleWrite(self.saveText.get(1.0, "end"), self.master.sharedData["SatelliteData"])
        if "SUCCESS" in result:
            self.master.unbind("<Return>", self.bindID)
            self.master.switchFrame(ReturnToMainPrompt)
        else:
            self.saveLabel.config(text=result)

class ShowCatCrawl(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        self.master.geometry("500x410")
        
        topFrame = tk.Frame(self)
        topFrame.pack(side="top", fill="both")
        self.scroll = tk.Scrollbar(topFrame)
        self.scroll.pack(side="right", fill="y")
        self.text = tk.Text(topFrame, yscrollcommand=self.scroll.set)
        self.text.pack(side="left", fill="both")
        self.text.config(state="disabled")
        self.scroll.config(command=self.text.yview)
        self.queue = queue.Queue()
        self.scrapeThread = CategoryThread(self.queue, self.master.sharedData["URL"], self.master.sharedData["APIKey"].get())
        self.scrapeThread.start()
        self.after(10, self.updater)
        
    def updater(self):   
        if self.scrapeThread.is_alive():
            item = self.queue.get()
            if item is None:
                self.after(10, self.updater)
            else:
                self.updateText(item)
                self.after(10, self.updater)
        else:
            if not self.queue.empty():
                item = self.queue.get()
                if item is not None:
                    self.updateText(item)
                    self.after(10, self.updater)
            else:        
                self.text.config(state="normal")
                self.text.insert("end", "All workers done, save your data!\n")
                self.text.config(state="disabled")
                self.text.yview_moveto(1.0)
                
                bottomFrame = tk.Frame(self)
                bottomFrame.pack(side="bottom")
                self.saveLabel = tk.Label(bottomFrame, text="Save to file: ")
                self.saveLabel.pack(side="left")  
                self.saveText = tk.Text(bottomFrame, height = 1)
                self.saveText.pack(side="right")
                self.bindID = self.master.bind("<Return>", self.handleReturn)                    
                return
    
    def updateText(self, item):
        self.master.sharedData["SatelliteData"].append(item[:-1])
        self.text.config(state="normal")
        self.text.insert("end", item[3] + "\n")
        self.text.config(state="disabled")
        self.text.yview_moveto(1.0)
            
    def handleReturn(self, event):
        result = handleWrite(self.saveText.get(1.0, "end"), self.master.sharedData["SatelliteData"])
        if "SUCCESS" in result:
            self.master.unbind("<Return>", self.bindID)
            self.master.switchFrame(ReturnToMainPrompt)
        else:
            self.saveLabel.config(text=result)
            
class CategoryListThreadScheduler(threading.Thread):
    def __init__(self, queue, categoryList, apiKey):
        threading.Thread.__init__(self)
        self.queue = queue
        self.categoryList = categoryList
        self.apiKey = apiKey
    def run(self):
        for pair in self.categoryList:
            categoryName = pair[0]
            categoryURL = pair[1]
            self.queue.put(categoryName, True, None)
            thread = CategoryThread(self.queue, categoryURL, self.master.sharedData["APIKey"].get())
            thread.start()
            thread.join()

class ShowCatListCrawl(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        self.master = master
        self.master.geometry("500x410")
        
        topFrame = tk.Frame(self)
        topFrame.pack(side="top", fill="both")
        self.scroll = tk.Scrollbar(topFrame)
        self.scroll.pack(side="right", fill="y")
        self.text = tk.Text(topFrame, yscrollcommand=self.scroll.set)
        self.text.pack(side="left", fill="both")
        self.text.config(state="disabled")
        self.scroll.config(command=self.text.yview)
        self.queue = queue.Queue()
        
    def updater(self):   
        if self.scrapeThread.is_alive():
            item = self.queue.get()
            if item is None:
                self.after(10, self.updater)
            else:
                self.updateText(item)
                self.after(10, self.updater)
        else:
            if not self.queue.empty():
                item = self.queue.get()
                if item is not None:
                    self.updateText(item)
                    self.after(10, self.updater)
            else:        
                self.text.config(state="normal")
                self.text.insert("end", "All workers done for this category\n")
                self.text.config(state="disabled")
                self.text.yview_moveto(1.0)
                
                result = handleWrite(self.categoryName + "Satellites.txt", self.master.sharedData["SatelliteData"])
                self.master.sharedData["SatelliteData"] = []
                return
    
    def updateText(self, item):
        self.master.sharedData["SatelliteData"].append(item[:-1])
        self.text.config(state="normal")
        self.text.insert("end", item[3] + "\n")
        self.text.config(state="disabled")
        self.text.yview_moveto(1.0)

class ReturnToMainPrompt(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self,master)
        tk.Label(self, text="Return to main menu?").pack()
        tk.Button(self, text="Yes", command = self.yesButton).pack(fill = "x")
        tk.Button(self, text="No", command = self.noButton).pack(fill = "x")
    def yesButton(self):
        self.master.switchFrame(CrawlerSelectionMenu)
    def noButton(self):
        sys.exit()

app = App()
app.mainloop()