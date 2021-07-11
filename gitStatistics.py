import requests
import argparse
import os
import json
import sys
import csv
import datetime
import re
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import urllib3

# just to prevent unnecessary logging since we are not verifying the host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

queryBase = """
query($repo: String!, $owner: String!, $branch: String!)
{
    repository(name: $repo, owner: $owner){
    ref(qualifiedName: $branch) {
      target {
        ... on Commit {
          id
        history(since: "2015-01-01T01:01:00") {
            pageInfo {
              hasNextPage
            }
            edges {
              node {
                oid
                message
                additions
                deletions
                author {
                  name
                  date
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

class gitStatistics:
    def __init__(self,args):
        #Initialize argument parser
        self.argParser = self.__initArgParser()
        self.args = self.argParser.parse_args(args)
        if not self.args.branch:
            self.args.branch = "master"
        #Create a session to set default call Header information
        self.session = requests.session()
        self.session.headers = {"Authorization":"token " + self.args.apiKey}
        self.session.verify = False
        #Set a default base URL for api calls
        if self.args.hostname:
            self.url = 'https://'+ self.args.hostname +'/api/graphql'
        else:
            self.url = 'https://api.github.com/graphql'

        #TODO: Change from user focused structure to Repository focused structure to enable
        #breakout reports based on individual repositories
        self.users = {}

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='Gathers statistics on activity in targetted GitHub Repositories, default selection are repositories within current directory')
        argParser.add_argument("apiKey", help = 'Github api key')
        argParser.add_argument("owners", help = 'Comma separated Owner(s) of targeted Repos')
        argParser.add_argument("--branch","--b", help = 'User defined target branch, default is master')
        argParser.add_argument("--hostname", "--hn", help = 'https://<user specified hostname>/api/graphql - use for enterprise')
        argParser.add_argument("--repos","--r", help = 'Comma separated repo(s) to analyze')
        argParser.add_argument("--addr", help = 'Address of a folder containing repos or csv containing repo names')
        argParser.add_argument("--wordCloud","--wc", help = 'Generates word clouds from commit messages', action = 'store_true')
        argParser.add_argument("--graphStats","--gs", help = 'Displays Simple Graphs of data', action = 'store_true')
        argParser.add_argument("--csv", help = 'Stores recorded data as a CSV', action = 'store_true')
        argParser.add_argument("--awards","--aw", help = 'Prints awards/titles for users based on their statistics', action = 'store_true')
        return argParser

    def makeWordCloud(self):
        #Prepare for creating subplot, calculate rows/cols
        plots = len(self.users)
        cols = np.ceil(np.sqrt(plots))
        rows = np.ceil(plots/cols)
        i = 1 #index of current plot, tells plt.subplot() where to place the wordCloud

        plt.figure(figsize = (cols*5,rows*5), facecolor = '#f5f5f5')
        #create a wordcloud for each recorded user
        for user in self.users:
            words = self.users.get(user)[3]#get saved commit messages
            if len(words) == 0:
                continue
            words = words.lower()#standardize case, TEST == test == TesT

            wordcloud = WordCloud(width = 800, height = 800,
            background_color ='#f5f5f5',
            stopwords = set(STOPWORDS), #filter out insignificant words
            min_font_size = 1).generate(words)

            #add wordcloud to subplot
            plt.subplot(int(rows),int(cols),i).set_title(user, fontweight = 'bold')
            plt.imshow(wordcloud)
            plt.axis("off")
            plt.tight_layout(pad = 1)
            i+=1 #iterate
        plt.savefig('gitStatWordCloud.png')

    def makeCSV(self):
        fields = ["User Name", "Additions", "Deletions", "Commits", "Commits per Weekday", "Commit Times"]
        with open('gitStatistics.csv', 'w') as csvOutput:
            outputWriter = csv.writer(csvOutput)
            outputWriter.writerow(fields)
            #Write each user to CSV
            for user in self.users:
                userStats = self.users.get(user)
                row = [user]#User Name
                row+=[userStats[0]]#Additions
                row+=[userStats[1]]#Deletions
                row+=[userStats[2]]#Commits
                row+=[userStats[4]]#Commits Per Weekday
                row+=[userStats[5]]#Commit Times
                outputWriter.writerow(row)

    def grantAwards(self):
        committedUser = None
        committedScore = None
        committedDate = None
        weekendUser = None
        weekendScore = None
        additionUser = None
        additionScore = None
        additionCommits = None
        sporadicUser = None
        sporadicScore = None
        consistentUser = None
        consistentScore = None
        hareUser = None
        hareScore = None
        tortiseUser = None
        tortiseScore = None
        verboseUser = None
        verboseScore = None
        earlyUser = None
        earlyScore = None
        lateUser = None
        lateScore = None
        for user in self.users:
            userStats = self.users.get(user)
            #Weekend Warrior
            userScore = userStats[4][5] + userStats[4][6]
            if weekendUser is not None:
                if userScore > weekendScore:
                    weekendUser = user
                    weekendScore = userScore
            else:
                weekendUser = user
                weekendScore = userScore
            #Committed Committer
            userScore =  userStats[2]
            if committedUser is not None:
                if userScore > committedScore:
                    committedUser = user
                    committedScore = userScore
                    committedDate = userStats[5][1]
            else:
                committedUser = user
                committedScore = userScore
                committedDate = userStats[5][1]
            #Heavy Hitter
            userScore = userStats[0] / userStats[2]
            if additionUser is not None:
                if userScore > additionScore:
                    additionUser = user
                    additionScore = userScore
                    additionCommits = userStats[2]
            else:
                additionUser = user
                additionScore = userScore
                additionCommits = userStats[2]
            #Sporadic/Consistent/hare Committer
            if userStats[2] > 2:
                try:
                    userTimeBetweenCommits = []
                    mean = 0
                    for i in range(userStats[2]-1):
                        curTime = userStats[5][i]
                        nextTime = userStats[5][i+1]
                        userTimeBetweenCommits += [nextTime-curTime]
                        mean += nextTime-curTime
                    mean = mean/len(userTimeBetweenCommits)
                    userScore = np.std(userTimeBetweenCommits)/mean*100
                    if sporadicUser is not None:
                        if userScore > sporadicScore:
                            sporadicUser = user
                            sporadicScore = userScore
                    else:
                        sporadicUser = user
                        sporadicScore = userScore
                    if consistentUser is not None:
                        if userScore < consistentScore:
                            consistentUser = user
                            consistentScore = userScore
                    else:
                        consistentUser = user
                        consistentScore = userScore
                    if hareUser is not None:
                        if mean < hareScore:
                            hareUser = user
                            hareScore = mean
                    else:
                        hareUser = user
                        hareScore = mean
                    if tortiseUser is not None:
                        if mean > tortiseScore:
                            tortiseUser = user
                            tortiseScore = mean
                    else:
                        tortiseUser = user
                        tortiseScore = mean
                except ZeroDivisionError:
                    pass
            #Verbose Committer
            userScore = len(userStats[3].split(" "))/userStats[2]
            if verboseUser is not None:
                if userScore > verboseScore:
                    verboseUser = user
                    verboseScore = userScore
            else:
                verboseUser = user
                verboseScore = userScore
            #Night Owl
            userScore = userStats[6]
            if lateUser is not None:
                if userScore > lateScore:
                    lateUser = user
                    lateScore = userScore
            else:
                lateUser = user
                lateScore = userScore
            #Early Bird
            userScore = userStats[7]
            if earlyUser is not None:
                if userScore > earlyScore:
                    earlyUser = user
                    earlyScore = userScore
            else:
                earlyUser = user
                earlyScore = userScore

        print(weekendUser,"is the WEEKEND WARRIOR with",weekendScore,"commits logged on weekends")
        print(committedUser,"is the COMMITTED COMMITTER with",committedScore,"commits logged since joining at",datetime.datetime.fromtimestamp(committedDate))
        print("Watch out for this HEAVY HITTER...",additionUser,"has averaged",int(additionScore),"additions over",additionCommits,"commits")
        print(sporadicUser,"is the most SPORADIC COMMITTER with a commit interval variation coefficient of",str(int(sporadicScore))+ "%")
        print(consistentUser,"is the most CONSISTENT COMMITTER with a commit interval variation coefficient of only ",str(int(consistentScore))+"%")
        print(tortiseUser,"is the TORTISE with a mean commit interval of",int(tortiseScore/60/60),"hours")
        print(hareUser,"is the HARE with a mean commit interval of only",int(hareScore/60/60),"hours")
        print(verboseUser,"is the most VERBOSE COMMITTER, averaging",verboseScore,"words per commit")
        print(earlyUser,"is an EARLY BIRD with the most early morning commits")
        print(lateUser,"is the NIGHT OWL with the most late night commits")

    def graphStats(self):
        additionBar=[] 
        deletionBar=[]
        userList = []
        
        #Put Addition and Deletion data in lists for plotting
        for user in self.users:
            additionBar.append(self.users.get(user)[0])
            deletionBar.append(self.users.get(user)[1])
            userList.append(user)

        with PdfPages('gitStatGraphs.pdf') as pdf:
            #Report Additions
            plt.figure(figsize = (12,10), facecolor = '#f5f5f5')
            plt.bar(userList,additionBar, color = '#6cc644',)
            plt.title("Additions per User", fontweight = 'bold')
            plt.ylabel("Number of Additions")
            plt.xticks(rotation = 90)#rotate names to prevent overlap if there are too many
            pdf.savefig()

            #Report Deletions
            plt.figure(figsize = (12,10), facecolor = '#f5f5f5')
            plt.bar(userList,deletionBar, color = '#bd2c00',)
            plt.title("Deletions per User", fontweight = 'bold')
            plt.ylabel("Number of Deletions")
            plt.xticks(rotation = 90)
            pdf.savefig()

            #Report Daily Commits
            dayNames = ["Mon","Tue","Wed","Thur","Fri","Sat","Sun"]
            commitDays = [0,0,0,0,0,0,0]
            #Sum commits per day of week
            for user in self.users:
                userDays = self.users.get(user)[5]
                for i in range(7):
                    commitDays[i] = commitDays[i] + userDays[i]
            plt.figure(figsize = (12,10), facecolor = '#f5f5f5')
            plt.bar(dayNames,commitDays, color = '#4078c0',)
            plt.title("Commits per day of Week", fontweight = 'bold')
            plt.ylabel("Number of Commits")
            pdf.savefig()

    def getStats(self):
        ##Compile list of target repositories
        repos = []
        #Load from address
        if self.args.addr:#If there is an addr to load from
            if "." in self.args.addr:#If the addr points to a .csv file, read each line
                if self.args.addr.split(".")[1] == "csv":
                    try:
                        with open(self.args.addr) as csvInput:
                            inputReader = csv.reader(csvInput)
                            for row in inputReader:
                                repos+=row     
                    except FileNotFoundError:
                        print("Indicated CSV does not exist")
                else:
                    print("Invalid file type")
                    return
            else:
                try:
                    repos = os.listdir(self.args.addr)
                except FileNotFoundError:
                    print("Invalid directory address")
                    return
        else:
            if self.args.repos:
                repos += self.args.repos.split(",")
            else:
                repos = os.listdir(os.curdir)

        #Load List of Repository Owners
        owners = self.args.owners.split(',')

        for repo in repos:
            for owner in owners:
                params = {"repo":repo,"owner":owner, 'branch':self.args.branch}
                response = self.session.post(self.url,json={'query':queryBase, 'variables':params})
                data = json.loads(response.text)
                data = data["data"]["repository"]

                if not data: #if the owner/repository combination is invalid, conitnue to next
                    continue

                data = data["ref"]
                if not data:
                    continue

                #parse data from response for each commit
                data = data["target"]["history"]["edges"]
                for commit in data:
                    commit = commit['node']
                    author = commit["author"]["name"]
                    date = commit["author"]["date"]
                    commitMessage = commit["message"]
                    additions = commit["additions"]
                    deletions = commit["deletions"]

                    commitDate = date.split('T')[0].split("-")
                    commitTime = date.split('T')[1].split(":")
                    nightOwl = 0
                    earlyBird = 0
                    if(int(commitTime[0])>=20):
                        nightOwl = 1
                    else:
                        if(int(commitTime[0])<=8):
                            earlyBird = 1
                    weekdayCheck = datetime.datetime(int(commitDate[0]),int(commitDate[1]),int(commitDate[2]),int(commitTime[0]),int(commitTime[1]))
                    sinceEpoch = weekdayCheck.timestamp()
                    weekdayCheck = weekdayCheck.weekday()#returns the day of week as an int 0=monday

                    if author not in self.users:
                        #create a new user with new data
                        weekdayCommitCount = [0,0,0,0,0,0,0]
                        weekdayCommitCount[weekdayCheck]+=1
                        commits = 1
                        commitTimes = [sinceEpoch]
                        self.users[author] = [additions, deletions,commits,commitMessage, weekdayCommitCount,commitTimes,nightOwl,earlyBird]
                    else:
                        #overwrite an existing user with combined data
                        user = self.users.get(author)
                        additions += user[0]
                        deletions += user[1]
                        commits = user[2] + 1
                        commitMessage += user[3]
                        weekendCommit = user[4]
                        weekendCommit[weekdayCheck]+=1
                        commitTimes = user[5] + [sinceEpoch]
                        commitTimes.sort()
                        nightOwl += user[6]
                        earlyBird += user[7]
                        self.users[author] = [additions, deletions,commits,commitMessage, weekdayCommitCount,commitTimes,nightOwl,earlyBird]

    def execute(self):
        self.getStats()
        if self.users != {}:
            if self.args.wordCloud:
                self.makeWordCloud()
            if self.args.graphStats:
                self.graphStats()
            if self.args.csv:
                self.makeCSV()
            if self.args.awards:
                self.grantAwards()

if __name__ == "__main__":
    engine = gitStatistics(sys.argv[1:])
    engine.execute()