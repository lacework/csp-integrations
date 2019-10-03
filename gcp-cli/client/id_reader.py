from helpers import filePathInput
from helpers import yesNoInput
from util.util import Util
import csv
import urllib

def readId(idType):
    while True:
        readFrom = raw_input("Do you want to read " + idType.lower() + " IDs from a file or from GCP? (File/Gcp): \n")
        readFrom = readFrom.lower()
        if readFrom == "file":
            return readFromFile(idType)
        elif readFrom == "gcp":
            return readFromGcp(idType)
        else:
            print "Enter valid input."

def readFromFile(idType):
    while True:
        yesOrNo = yesNoInput("Verify the file is using a valid CSV format with IDs under the column called 'Name'! (Y/N): \n")
        if yesOrNo == "y" or yesOrNo == "yes":
            return readFromCsv(idType)
        else:
            print "Reformat the CSV file to the correct format."

def readFromCsv(idType):
    filePath = filePathInput("Enter the full directory path to the " + idType.lower() + " IDs CSV file:\n")
    auditIds = []
    with open(filePath) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        index_count = 0
        index = 0
        for row in csv_reader:
            if line_count == 0:
                for entry in row:
                    if entry.lower() == "name":
                        index = index_count
                        break
                    index_count += 1
            else:
                auditIds.append(row[index])
            line_count += 1

    return auditIds

def readFromGcp(idType):
    util = Util()
    if idType == "PROJECT":
        return getProjectsFromGcp(util, "The following projects will be loaded: \n")
    elif idType == "FOLDER":
        while True:
            parentType = raw_input("Enter parent type for folders you want to get? (Organization/Folder): \n")
            parentType = parentType.lower() + "s"
            if parentType == "organizations" or parentType == "folders":
                while True:
                    parentId = raw_input("Enter " + parentType + " id: \n")
                    if " " in parentId or parentId == "":
                        print "Enter valid input. "
                        continue
                    parent = parentType + "/" + parentId
                    break
            else:
                print "Enter valid input."
                continue
            yesOrNo = yesNoInput("Parent defined as: " + parent + "\nIs that correct? (Y/N): \n")
            if yesOrNo == "y" or yesOrNo == "yes":
                parent = urllib.quote(parent)
                folderList = util.getFolderList(parent)
                if folderList is None:
                    print "No folders found, reenter the parent or check if you have proper permissions for folders or parent you are looking for!"
                    continue
                else:
                    folderNames = [str(folder['displayName']) for folder in folderList]
                    folderIds = [str(folder['name']).replace("folders/", "") for folder in folderList]
                    yesOrNo = yesNoInput("The following folders will be loaded: \n" + str(folderNames) + "\nConfirm? (Y/N): \n")
                    if yesOrNo == "y" or yesOrNo == "yes":
                        return folderIds


def getProjectsFromGcp(util, finalMsg):
    while True:
        filter = ""
        yesOrNo = yesNoInput("Do you want to filter the project list? (Y/N):\n")
        if yesOrNo == "y" or yesOrNo == "yes":
            filterName = raw_input("Filter by name? Example: \nproject1: searches for exact string\nproject*: searches for projects containing string \n(If you do not want a filter, just enter return.): \n")
            if filterName is not " " and filterName is not "":
                filter = filter + "name:" + filterName + " "
            filterId = raw_input("Filter by ID? Example: \nproject1: searches for the exact string\nproject*: searches for projects containing the string \n(If you do not want a filter, just enter return.): \n")
            if filterId is not " " and filterId is not "":
                filter = filter + "id:" + filterId + " "
            filterLabel = raw_input("Filter projects by labels? (If you do not want a filter, just enter return.): \n")
            if filterLabel is not " " and filterLabel is not "":
                filterLabelValue = raw_input("For " + filterLabel + " do you want to also filter by value? (If you do not want a filter, just enter return.): \n")
                if filterLabelValue is not " " and filterLabelValue is not "":
                    filter = filter + "labels." + filterLabel  + ":" + filterLabelValue + " "
                else:
                    filter = filter + "labels." + filterLabel  + ":* "
            yesOrNo = yesNoInput("Do you want to add more filters? (Y/N): \n")
            if yesOrNo == "y" or yesOrNo == "yes":
                continue
            yesOrNo = yesNoInput("The following filters have been defined: \n" + filter + "\nIs that correct? (Y/N): \n")
            if yesOrNo == "n" or yesOrNo == "no":
                print "Reenter your filters!"
                continue

            filter = filter[:-1]
            filter = urllib.quote(filter)
            projectList = util.getProjectList(filter)
            if projectList is None:
                print "No projects found, reenter your filters or check if you have the required permissions for projects you are searching for!"
            else:
                projectIds = [str(project['projectId']) for project in projectList]
                print finalMsg
                for i in range(1, len(projectIds)+1):
                    print str(i) + ". " + projectIds[i-1]
                yesOrNo = yesNoInput("\nConfirm Projects? (Y/N): \n")
                if yesOrNo == "y" or yesOrNo == "yes":
                    return projectIds
        elif yesOrNo == "n" or yesOrNo == "no":
            projectList = util.getProjectList()
            if projectList is None:
                print "No projects found, reenter your filters or check if you have the required permissions for projects you are searching for!"
            else:
                projectIds = [str(project['projectId']) for project in projectList]
                print finalMsg
                for i in range(1, len(projectIds)+1):
                    print str(i) + ". " + projectIds[i-1]
                yesOrNo = yesNoInput("\nConfirm Projects? (Y/N): \n")
                if yesOrNo == "y" or yesOrNo == "yes":
                    return projectIds
