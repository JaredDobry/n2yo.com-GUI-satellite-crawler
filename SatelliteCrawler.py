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
import os
import time
import sys
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import filedialog

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
        if not len(out) == 3:
            out = ["", "", "", "Link had no data"]
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

#Schedules and joins all threads that will do requests queries for information
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
            time.sleep(.1) #Be nice and don't flood the webiste with requests
            
        #Join all threads
        for t in threads:
            t.join()  
            
        return

#Root app class that is the container for all Tk frames, holds the shared data passed around from frame to frame        
class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.data = {
            "url" : "",
            "apikey" : "",
            "isCategory" : False,
            "scrapeTable" : [],
            "categoryList" : [],
            "writeTable" : {}
            }
        self.data["apikey"] = "NONE"
        self.title("Satellite Crawler")
        self._frame = None
        self.switchFrame(MainMenuDisplay)
    
    #Destroys the current active frame and creates a new one, calling its run function after __init__
    def switchFrame(self, frameClass):
        self.geometry("")
        newFrame = frameClass(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = newFrame
        self._frame.pack(expand = "true", fill = "both")
        self._frame.run()

#Appends the text widget with the new line of text to display
def UpdateText(frame, text):
    frame.text.config(state="normal")
    frame.text.insert("end", text + "\n")
    frame.text.config(state="disabled")
    frame.text.yview_moveto(1.0)

#Sets up a text widget on the supplied frame, with disabled input
def SetupDisplay(frame):
    topFrame = tk.Frame(frame)
    topFrame.pack(side = "top", fill="both", expand = "true")
    frame.text = tk.Text(topFrame)
    frame.text.pack(side="top", fill="both", expand = "true")
    frame.text.config(state="disabled")

#Sets up a text widget with an attached scroll bar, text input disabled
def SetupDisplayWithScroll(frame):
    topFrame = tk.Frame(frame)
    topFrame.pack(side = "top", fill="both", expand = "true")
    frame.scroll = tk.Scrollbar(topFrame)
    frame.scroll.pack(side="right", fill="y", expand = "true")
    frame.text = tk.Text(topFrame, yscrollcommand=frame.scroll.set)
    frame.text.pack(side="left", fill="both", expand = "true")
    frame.text.config(state="disabled")
    frame.scroll.config(command=frame.text.yview)

#Adds a text widget and label widget to the bottom of the frame to allow the user to save
def SetupSaveText(frame):
    bottomFrame = tk.Frame(frame)
    bottomFrame.pack(side = "bottom", fill = "both", expand = "true")
    frame.label = tk.Label(bottomFrame, text="Save to:")
    frame.label.pack(side="left")
    frame.saveText = tk.Text(bottomFrame, height = 1, width = 10)
    frame.saveText.insert("end", "Save.txt")
    frame.saveText.pack(side="right", fill = "x", expand = "true")
    frame.bindID = frame.master.bind("<Return>", frame._SaveReturn)

#Creates a dialog box prompting the user to continue using the application or not
def CreateReturnToMainDialog(frame):
    answer = messagebox.askyesno("Return to main menu", "Return to main menu?")
    if answer:
        ReturnToMain(frame)
    else:
        CloseApp(frame)

#Creates an input dialog box with the label text given
def CreateURLDialog(frame, labelText):
    return simpledialog.askstring("URL input", labelText, parent = frame)

#Creates an input dialog prompting the user if they have a file with the list of things to scrape
def CreateFileSelectionDialog(frame, labelText):
    return messagebox.askyesno("File selection", labelText)

#Creates a file selection dialog box
def CreateFileExplore(frame):
    my_filetypes = [('all files', '.*'), ('text files', '.txt')]
    return filedialog.askopenfilename(parent=frame, initialdir=os.getcwd(), title="Please select a file:", filetypes=my_filetypes)

#Removes all \n characters from a str input
def ParseReturnCharacters(text):
    try:
        ind = text.index("\n")
        if ind == len(text) - 1:
            newText = text[:-1]
        else:
            newText = text[:ind] + text[ind + 1:]
        return ParseReturnCharacters(newText)
    except ValueError:
        return text

#Handles the save operation on a return input. Checks for filename validity
def SaveReturn(frame):
    input = frame.saveText.get(1.0, "end")
    filename = ParseReturnCharacters(input)
    frame.saveText.delete(1.0, "end")
    try:
        fw = open(filename, "w")
        #Grab the info out of the write table
        for cat in frame.master.data["writeTable"]:
            for satData in frame.master.data["writeTable"][cat]:
                if not satData[0] == "":
                    for entry in satData:
                        fw.write(entry + "\n")
        fw.close()
        frame.master.unbind("<Return>", frame.bindID)
        UpdateText(frame, "Write to file: " + filename +" sucessful")
    except IOError:
        frame.label.config(text="Error opening file: " + filename)
    CreateReturnToMainDialog(frame)

#Handles the save operation of all categories when we do a category list scrape
def SaveCategoryList(frame):
    for cat in frame.master.data["writeTable"]:
        try:
            fw = open(cat + "Satellites.txt", "w")
            for satData in frame.master.data["writeTable"][cat]:
                for entry in satData:
                    fw.write(entry + "\n")
            fw.close()
            UpdateText(frame, "Write to file: " + cat + "Satellites.txt sucessful")
        except IOError:
            UpdateText(frame, "[ERROR] Write to file: " + cat + "Satellites.txt FAILED")

def SaveListToFile(frame, isCategory, filename):
    if isCategory:
        try:
            fw = open(filename, "w")
            for item in frame.master.data["categoryList"]:
                fw.write("CategoryName=" + item[0] + " URL=" + item[1] + "\n")
            fw.close()
            return True
        except IOError:
            return False
    else:
        try:
            fw = open(filename, "w")
            for url in frame.master.data["scrapeTable"][0][1]:
                fw.write(url + "\n")
            fw.close()
            return True
        except IOError:
            return False

#Reads a satellite list or category list, and places the url data into the scrape table, returns false if there was an error
def ReadFileList(frame, filename):
    try:
        fr = open(filename, "r")
        lines = fr.readlines()
        satURLS = []
        for line in lines:
            if "CategoryName= " in line:
                try:
                    indCatEnd = line.index(" ")
                    indURL = line.index("URL=")
                    category = line[:indCatEnd - 1]
                    url = line[indURL + 4:]
                    if "\n" in url:
                        url = url[:-1]
                    frame.master.data["scrapeTable"].append(category, url)
                except ValueError:
                    return false
            else:
                if "n2yo" in line:
                    url = line
                    try:
                        ind = line.index("\n")
                        url = line[:ind]
                    except ValueError: ()
                    satURLS.append(url)
        if not satURLS == []:
            frame.master.data["scrapeTable"].append(["NONE", satURLS])
        return True
    except IOError:
        return False

#Starts the thread manager for scraping and gives the frame a member variable for reference to it
def StartThreadManager(frame):
    frame.q = queue.Queue() 
    #start scraper thread
    frame.threadmanager = ThreadManager(frame.q, frame.master.data["scrapeTable"], frame.master.data["apikey"])
    frame.threadmanager.start()   
    #update gui
    frame.after(16, frame.updater()) #roughly 60 fps   

#Updater function that appends status messages to the text view as they come from thread workers into the queue
#Calls OnComplete when all threads are dead
def UpdaterList(frame):
    try:
        item = frame.q.get(False)
        if item is not None:
            if item[0] not in frame.master.data["writeTable"]:
                frame.master.data["writeTable"][item[0]] = [item[1][:-1]]
            else:
                frame.master.data["writeTable"][item[0]].append(item[1][:-1])
            UpdateText(frame, "Status: " + item[1][3])
        frame.after(16, frame.updater)
    except queue.Empty:
        if frame.threadmanager.is_alive():
            frame.after(16, frame.updater)
        else:
            UpdateText(frame, "\n[Complete]")
            frame.OnComplete()
            return

#Clears the shared data and puts you back on the main menu
def ReturnToMain(frame):
    frame.master.data["url"] = ""
    frame.master.data["isCategory"] = False
    frame.master.data["scrapeTable"] = []
    frame.master.data["categoryList"] = []
    frame.master.data["writeTable"] = {}
    frame.master.switchFrame(MainMenuDisplay)

#Terminates the application    
def CloseApp(frame):
    frame.master.destroy()

#Checks if this URL is valid
def TestURLValid(url):
    if "c=" in url:
        if not "www.n2yo.com/satellites/?c=" in url:
            return False
        else:
            try:
                requests.get(url)
                return True
            except Exception:
                return False
    elif "s=" in url:
        if not "www.n2yo.com/satellite/?s=" in url:
            return False
        else:
            try:
                requests.get(url)
                return True
            except Exception:
                return False

#Displays the main menu options
class MainMenuDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)
        #set up UI
        tk.Button(self, text="Single satellite", command = self.SatPress).pack(fill="x", expand = "true")
        tk.Button(self, text="List of satellites", command=self.SatListPress).pack(fill="x", expand = "true")
        tk.Button(self, text="Satellite category", command=self.CatPress).pack(fill="x", expand = "true")
        tk.Button(self, text="List of categories", command=self.CatListPress).pack(fill="x", expand = "true")

    def run(self):
        if self.master.data["apikey"] == "NONE":
            if messagebox.askyesno("Use API Key", "Use an API key?"):
                if messagebox.askyesno("Satellite Crawler", "Is the API Key in a file?"):
                    my_filetypes = [('all files', '.*'), ('text files', '.txt')]
                    filename = filedialog.askopenfilename(parent=self, initialdir=os.getcwd(), title="Please select a file:", filetypes=my_filetypes)
                    try:
                        fr = open(filename, "r")
                        key = fr.readline()
                        if not len(key) == 25:
                            messagebox.showerror("Satellite Crawler", "API Key invalid, ignoring it")
                        else:
                            self.master.data["apikey"] = key
                            messagebox.showinfo("Satellite Crawler", "API Key loaded")
                    except IOError:
                        messagebox.showerror("Satellite Crawler", "Error opening file " + filename + " for reading")
                        self.run()
                else:
                    key = simpledialog.askstring("Satellite Crawler", "API Key:", parent=self)
                    if not len(key) == 25:
                        messagebox.showerror("Satellite Crawler", "API Key invalid, ignoring it")
                    else:
                        self.master.data["apikey"] = key
                        if messagebox.askyesno("Satellite Crawler", "Save the key?"):
                            filename = simpledialog.askstring("Satellite Crawler", "Filename: ", parent=self)
                            try:
                                fw = open(filename, "w")
                                fw.write(key)
                                fw.close()
                                messagebox.showinfo("Satellite Crawler", "Writing API Key to " + filename + " sucessful")
                            except IOError:
                                messagebox.showerror("Satellite Crawler", "Error opening " + filename + " for writing")

    def SatPress(self):
        self.master.data["url"] = CreateURLDialog(self, "Satellite URL:")
        fixurl = self.master.data["url"]
        try:
            ind = fixurl.index("\n")
            fixurl = fixurl[:ind]
        except ValueError: ()
        if not TestURLValid(fixurl) or "www.n2yo.com/satellite/?s=" not in fixurl:
            messagebox.showerror("Satellite Crawler", "Invalid URL")
            self.SatPress()
        self.master.switchFrame(SatelliteDisplay)

    def SatListPress(self):
        if CreateFileSelectionDialog(self, "Do you have a file with the satellites to scrape?"):
            filename = CreateFileExplore(self)
            if not ReadFileList(self, filename):
                messagebox.showerror("Satellite Crawler",  "Error reading file: " + filename)
                self.SatListPress()
            else:
                self.master.switchFrame(SatelliteListDisplay)
        else:
            self.master.switchFrame(ListInputDisplay)

    def CatPress(self):
        self.master.data["url"] = CreateURLDialog(self, "Category URL:")
        fixurl = self.master.data["url"]
        try:
            ind = fixurl.index("\n")
            fixurl = fixurl[:ind]
        except ValueError: ()
        if not TestURLValid(fixurl) or "www.n2yo.com/satellites/?c=" not in fixurl:
            messagebox.showerror("Satellite Crawler", "Invalid URL")
            self.CatPress()
        self.master.switchFrame(CategoryDisplay)

    def CatListPress(self):
        self.master.data["isCategory"] = True
        if CreateFileSelectionDialog(self, "Do you have a file with the categories to scrape?"):
            filename = CreateFileExplore(self)
            if not ReadFileList(self, filename):
                messagebox.showerror("Satellite Crawler",  "Error reading file: " + filename)
                self.CatListPress()
            else:
                self.master.switchFrame(CategoryListDisplay)
        else:
            self.master.switchFrame(ListInputDisplay)

#Displays the output from scraping a single satellite        
class SatelliteDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)
        #set up UI
        SetupDisplay(self)

    def run(self):
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
                #Add return to main menu button
                tk.Button(self, text="Return to main menu", command = self._ReturnToMain).pack(side = "left", fill = "x", expand = "true")
                tk.Button(self, text="Close", command = self._CloseApp).pack(side = "left", fill = "x", expand = "true")
                return 

    def _ReturnToMain(self):
        ReturnToMain(self)

    def _CloseApp(self):
        CloseApp(self)

#Displays the output from scraping a list of satellites, prompts user for a file to save to
class SatelliteListDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)
        SetupDisplayWithScroll(self)

    def run(self):
        StartThreadManager(self)

    def updater(self):
        UpdaterList(self)
    
    def OnComplete(self):
        SetupSaveText(self)
        #Write out the data to the file specified by the user when they hit return
    def _SaveReturn(self, event):
        SaveReturn(self)

#Displayes the output from scraping a category of satellites, prompts user for a file to save to
class CategoryDisplay(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self,master)
        SetupDisplayWithScroll(self)

    def run(self):
        catlist = []
        catlist.append(["NONE", scrapeCategory(self.master.data["url"])])
        self.master.data["scrapeTable"] = catlist       
        StartThreadManager(self)

    def updater(self):
        UpdaterList(self)

    def OnComplete(self):
        SetupSaveText(self)

    def _SaveReturn(self, event):
        SaveReturn(self)

#Displays the output from scraping a list of categories of satellites, automatically saves to output files named after each category        
class CategoryListDisplay(tk.Frame):
    def __init__(self, master):  
        tk.Frame.__init__(self, master)
        #Set up UI elements
        SetupDisplayWithScroll(self)
    
    def run(self):
        StartThreadManager(self)
        
    def updater(self):
        UpdaterList(self)

    def OnComplete(self):
        SaveCategoryList(self)
        CreateReturnToMainDialog(self)

class ListInputDisplay(tk.Frame):
    def __init__(self,master):
        tk.Frame.__init__(self, master)
        #Set up UI elements
        self.isCategory = self.master.data["isCategory"]
        if self.isCategory:
            self.topFrame = tk.Frame(self)
            self.topFrame.pack(side = "top", fill = "both", expand = "true")
            tk.Button(self.topFrame, text="Add category", command = self.AddCategory).pack(side = "top", fill = "x", expand = "true")
            self.categoryFrames = []
            self.AddCategory()
        else:
            tk.Label(self, text="Please input all satellite URLs for this list").pack(side = "top", fill = "x", expand = "true")
            SetupDisplayWithScroll(self)
            self.text.config(state="normal")
        bottomFrame = tk.Frame(self)
        bottomFrame.pack(side="bottom", fill = "both", expand = "true")
        tk.Button(bottomFrame, text="Done", command = self.DoneButton).pack(side = "left", fill = "x", expand = "true")
        tk.Button(bottomFrame, text="Cancel", command = self.CancelButton).pack(side = "right", fill = "x", expand = "true")


    def run(self): ()

    def AddCategory(self):
        newFrame = tk.Frame(self.topFrame)
        newFrame.pack(side = "top", fill = "both", expand = "true")
        tk.Label(newFrame, text="Category:").pack(side="left", fill = "x", expand = "true")
        newFrame.categoryText = tk.Text(newFrame, height = 1, width = 20, fill = "x", expand = "true")
        newFrame.categoryText.pack(side = "left")
        tk.Label(newFrame, text="URL:").pack(side="left", fill = "x", expand = "true")
        newFrame.URLText = tk.Text(newFrame, height = 1, width = 40, fill = "x", expand = "true")
        newFrame.URLText.pack(side = "left")
        self.categoryFrames.append(newFrame)

    def DoneButton(self):
        if self.isCategory:
            catlist = []
            for categoryFrame in self.categoryFrames:
                category = categoryFrame.categoryText.get(1.0, "end")
                url = categoryFrame.URLText.get(1.0, "end")
                try:
                    ind = category.index("\n")
                    category = category[:ind]
                    ind = url.index("\n")
                    url = url[:ind]
                except ValueError: ()
                if not url == "":
                    catlist.append([category, scrapeCategory(url)])
                    self.master.data["categoryList"].append([category, url])
            self.master.data["scrapeTable"] = catlist
        else:
            allText = self.text.get(1.0, "end")
            array = putStringIntoArray(allText)
            fixarray = []
            for entry in array:
                if not entry == "":
                    fixarray.append(entry)
            self.master.data["scrapeTable"].append(["NONE", fixarray])

        if messagebox.askyesno("Save list to file", "Save category/list to file?"):
            filename = simpledialog.askstring("Save", "Save to file:")
            if not SaveListToFile(self, self.isCategory, filename):
                messagebox.showerror("Satellite Crawler",  "Error saving file: " + filename)
            else:
                messagebox.showinfo("Satellite Crawler",  "Sucess in writing file: " + filename)

        if self.isCategory:
            self.master.switchFrame(CategoryListDisplay)
        else:
            self.master.switchFrame(SatelliteListDisplay)

    def CancelButton(self):
        self.master.switchFrame(MainMenuDisplay)

 
#Program entry point, starts up the UI
app = App()
app.mainloop()
