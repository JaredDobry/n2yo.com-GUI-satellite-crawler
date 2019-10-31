import sys

#reads in our config pointing us at all of the satellite lists to generate players for
def readConfig():
    try:
        f = open("WriterConfig.txt", 'r')
        lines = f.readlines()
        data = []
        for line in lines:
            if "\n" in line:
                ind = line.index("\n")
                data.append(line[0:ind])
            else:
                data.append(line)
        return data
    except IOError:
        sys.exit("[ERROR] Could not open 'WriterConfig.txt', please verify you have created the config file")

def appendBeginning(filename):
    try:
        fw = open(filename, "w")
        fw.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        fw.write("<NgtsPlayerTemplateLibrary>\n")
        fw.write("    <Header>\n")
        fw.write("        <Classification>UNCLASSIFIED//FOR OFFICIAL USE ONLY</Classification>\n")
        fw.write("        <Author>satellite.generator</Author>\n")
        fw.write("        <Source>Python Script</Source>\n")
        fw.write("        <Description>Desc</Description>\n")
        fw.write("        <FileVersion unit=\"NVersion\">0.0.0.0.1.0</FileVersion>\n")
        fw.write("        <SourceVersion unit=\"NVersion\">3.2.3.0.0.0</SourceVersion>\n")
        fw.write("    </Header>\n")
        fw.write("    <Contents>\n")
        fw.write("        <PlayerBuilders>\n")
        fw.close()
    except IOError:
        sys.exit("[ERROR] Error opening file " + filename + " for writing")
 
def appendEnding(filename):
    try:
        fw = open(filename, "a")
        fw.write("        </PlayerBuilders>\n")
        fw.write("    </Contents>\n")
        fw.write("</NgtsPlayerTemplateLibrary>")
        fw.close()
    except IOError:
        sys.exit("[ERROR] Error opening file " + filename + " for writing")
        
def appendBeginningGroup(filename, category):
    try:
        fw = open(filename, "w")
        fw.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        fw.write("<NgtsPlayerTemplateLibrary>\n")
        fw.write("    <Header>\n")
        fw.write("        <Classification>UNCLASSIFIED//FOR OFFICIAL USE ONLY</Classification>\n")
        fw.write("        <Source>Python Script</Source>\n")
        fw.write("        <Title>" + "All" + category + "Satellites" + "</Title>\n")
        fw.write("        <SourceVersion unit=\"NVersion\">3.2.3.0.0.0</SourceVersion>\n")
        fw.write("    </Header>\n")
        fw.write("    <Contents>\n")
        fw.write("        <PlayerBuilderGroup GroupName=\"" + "All" + category + "Satellites" + "\">\n")
        fw.write("            <Info>\n")
        fw.write("                <MenuCategories unit=\"std::vector&lt;std::string>\">[1]{Space|Groups}</MenuCategories>\n")
        fw.write("                <MenuDisplayName unit=\"std::string\">" + "All" + category + "Satellites" + "</MenuDisplayName>\n")
        fw.write("            </Info>\n")
    except IOError:
        sys.exit("[ERROR] Error opening file " + filename + " for writing")

def appendEndingGroup(filename):
    try:
        fw = open(filename, "a")
        fw.write("        </PlayerBuilderGroup>\n")
        fw.write("    </Contents>\n")
        fw.write("</NgtsPlayerTemplateLibrary>")
        fw.close()
    except IOError:
        sys.exit("[ERROR] Error opening file " + filename + " for writing")

def generatePlayer(filename):
    try:
        fr = open(filename, 'r')
        #parse the .txt off and make a file with .xml
        ind = filename.index(".txt")
        newfile = filename[0:ind] + ".xml"
        appendBeginning(newfile)
        fw = open(newfile, 'a')
        lines = fr.readlines()
        sat = []
        count = 0
        ind = filename.index("Satellite")
        cat = filename[:ind]
        for line in lines:
            editLine = line
            if "\n" in line:
                ind = line.index("\n")
                editLine = line[0:ind]
            sat.append(editLine)
            count += 1
            if count == 3:
                print("Writing satellite: " + sat[0] + " to " + cat + " player template")
                #parse this satellite
                fw.write("            <PlayerTemplate nodeCount=\"2\" userName=\"" + sat[0] + "\">\n")
                fw.write("                <Info>\n")
                fw.write("				    <MenuCategories unit=\"std::vector&lt;std::string>\">[1]{Space|" + cat + "}</MenuCategories>\n")
                fw.write("                    <MenuDisplayName unit=\"std::string\">" + sat[0] + "</MenuDisplayName>\n")
                fw.write("                    <ReferenceData unit=\"std::string\"/>\n")
                fw.write("                    <SecurityClassification unit=\"std::string\">UNCLASSIFIED//FOR OFFICIAL USE ONLY</SecurityClassification>\n")
                fw.write("                </Info>\n")
                fw.write("                <Model classVersion=\"0.0.2\" alias=\"" + sat[0] + "\" className=\"NgtsEntity\" dllNamespace=\"StdPlugins\">\n")
                fw.write("                    <Descriptor tag=\"Category\">StdPlugins</Descriptor>\n")
                fw.write("                    <Descriptor tag=\"Component\">/UNCLASSIFIED/PlayerComponents/StdPlugins/NgtsEntity/NgtsEntity.xml</Descriptor>\n")
                fw.write("                    <Descriptor tag=\"SubCategory\">NgtsEntity</Descriptor>\n")
                fw.write("                    <PropertyList/>\n")
                fw.write("                    <Interface fileId=\"0\" className=\"NGTS::PEntity\">\n")
                fw.write("                        <PropertyList>\n")
                fw.write("                            <DisEnum unit=\"NGTS::Entity::EntityType\">1.5.255.2.0.0.0</DisEnum>\n")
                fw.write("                            <Marking unit=\"std::string\">" + sat[0] + "</Marking>\n")
                fw.write("                        </PropertyList>\n")
                fw.write("                    </Interface>\n")
                fw.write("                    <Model classVersion=\"3.2.2\" alias=\"SatelliteMotionModel\" className=\"SatelliteMotionModel\" dllNamespace=\"StdMotionPlugins\">\n")
                fw.write("                        <PropertyList>\n")
                fw.write("                            <ConfigFile unit=\"NFilePath\">" + filename + "</ConfigFile>\n")
                fw.write("                            <Name unit=\"std::string\">" + sat[0] + "</Name>\n")
                fw.write("                        </PropertyList>\n")
                fw.write("                        <Interface fileId=\"0\" className=\"NGTS::PKinetic\">\n")
                fw.write("                            <PropertyList/>\n")
                fw.write("                        </Interface>\n")
                fw.write("                        <Interface fileId=\"0\" className=\"NGTS::PSatellite\">\n")
                fw.write("                            <PropertyList/>\n")
                fw.write("                        </Interface>\n")
                fw.write("                    </Model>\n")
                fw.write("                </Model>\n")
                fw.write("            </PlayerTemplate>\n")
                sat = []
                count = 0
        fr.close()
        fw.close()
        appendEnding(newfile)
    except IOError:
        sys.exit("[ERROR] Could not open file: " + filename + " for reading")
        
def generatePlayerGroup(filename):
    try:
        fr = open(filename, 'r')
        lines = fr.readlines()
        #parse the .txt off and make a file with .xml
        ind = filename.index(".txt")
        newfile = filename[0:ind] + "GroupTemplate.xml"
        ind = filename.index("Satellite")
        cat = filename[:ind]
        appendBeginningGroup(newfile, cat)
        fw = open(newfile, 'a')
        sat = []
        count = 0
        refId = 1
        fileId = 1
        for line in lines:
            editLine = line
            if "\n" in line:
                ind = line.index("\n")
                editLine = line[0:ind]
            sat.append(editLine)
            count += 1
            if count == 3:
                print("Writing satellite: " + sat[0] + " to " + cat + " group template")
                #parse this satellite
                fw.write("            <PlayerInstance userName=\"" + sat[0] + "\" nodeCount=\"2\">\n")
                fw.write("                <TemplateReference>\n")
                fw.write("                    <TemplateFilePath></TemplateFilePath>\n")
                fw.write("                    <TemplateName>" + sat[0] + "</TemplateName>\n")
                fw.write("                </TemplateReference>\n")
                fw.write("                <Model alias=\"" + sat[0] + "\" dllNamespace=\"StdPlugins\" className=\"NgtsEntity\" classVersion=\"0.0.2\">\n")
                fw.write("                    <Descriptor tag=\"Category\">StdPlugins</Descriptor>\n")
                fw.write("                    <Descriptor tag=\"Component\">/UNCLASSIFIED/PlayerComponents/StdPlugins/NgtsEntity/NgtsEntity.xml</Descriptor>\n")
                fw.write("                    <Descriptor tag=\"SubCategory\">NgtsEntity</Descriptor>\n")
                fw.write("                    <Interface className=\"NGTS::PEntity\" fileId=\"" + str(fileId) + "\">\n")
                fileId += 1
                fw.write("                        <PropertyList>")
                fw.write("                            <AppearanceBits unit=\"NGTS::Entity::AppearanceBits\">Bit22</AppearanceBits>\n")
                fw.write("                            <Marking unit=\"std::string\">" + sat[0] + "</Marking>\n")
                fw.write("                            <ReferEntityId unit=\"NGTS::Entity::NReferEntityId\">::" + str(refId) + "</ReferEntityId>\n")
                refId += 1
                fw.write("                        </PropertyList>\n")
                fw.write("                    </Interface>\n")
                fw.write("                    <Model alias=\"SatelliteMotionModel\" dllNamespace=\"StdMotionPlugins\" className=\"SatelliteMotionModel\" classVersion=\"3.2.2\">\n")
                fw.write("                        <Interface className=\"NGTS::PKinetic\" fileId=\"" + str(fileId) + "\">\n")
                fileId += 1
                fw.write("                            <PropertyList>\n")
                fw.write("                                <Geodetic unit=\"Earthlib::Geodetic\">0,0,0</Geodetic>\n")
                fw.write("                                <Heading unit=\"Mathlib::Radian\">0</Heading>\n")
                fw.write("                                <Pitch unit=\"Mathlib::Radian\">0</Pitch>\n")
                fw.write("                                <Roll unit=\"Mathlib::Radian\">0</Roll>\n")
                fw.write("                                <Speed unit=\"Mathlib::MeterPerSecond\">0</Speed>\n")
                fw.write("                            </PropertyList>\n")
                fw.write("                        </Interface>\n")
                fw.write("                    </Model>\n")
                fw.write("                </Model>\n")
                fw.write("            </PlayerInstance>\n")
                sat = []
                count = 0
        fr.close()
        fw.close()
        appendEndingGroup(newfile)
    except IOError:
        sys.exit("[ERROR] Could not open file: " + filename + " for reading")

def userSelection():
    print("Please make a selection:")
    print("[1] Create player templates")
    print("[2] Create player group templates")
    print("[3] Create both [1] and [2]")
    userInput = input()
    if userInput == "1":
        return 1
    elif userInput == "2":
        return 2
    elif userInput == "3":
        return 3
    else:
        print("\n [ERROR] Invalid selection, please input 1, 2, or 3\n")
        return userSelection()
               
#Main function
selection = userSelection()
#Grab our files to read from the config
files = readConfig()
for file in files:
    if selection == 1:
        generatePlayer(file)
    elif selection == 2:
        generatePlayerGroup(file)
    elif selection == 3:
        generatePlayer(file)
        generatePlayerGroup(file)