import requests
import argparse
import os
import json
import sys
import csv
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from wordcloud import WordCloud, STOPWORDS
import urllib3

# just to prevent unnecessary logging since we are not verifying the host
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

queryBase = """
query($repo: String!, $owner: String!)
{
    repository(name: $repo, owner: $owner){
    ref(qualifiedName: "master") {
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
        self.dayOfWeek  = [0,0,0,0,0,0,0]

    #Define arguments which the user may be prompted for
    @staticmethod
    def __initArgParser():
        argParser = argparse.ArgumentParser(description='Gathers statistics on activity in targetted GitHub Repositories, default selection are repositories within current directory')
        argParser.add_argument("apiKey", help = 'Github api key')
        argParser.add_argument("owners", help = 'Comma separated Owner(s) of targeted Repos')
        argParser.add_argument("--hostname", "--hn", help = 'https://<user specified hostname>/api/graphql - use for enterprise')
        argParser.add_argument("--repos","--r", help = 'Comma separated repo(s) to analyze')
        argParser.add_argument("--addr", help = 'Address of a folder containing repos or csv containing repo names')
        argParser.add_argument("--wordCloud","--wc", help = 'Generates word clouds from commit messages', action = 'store_true')
        argParser.add_argument("--graphStats","--gs", help = 'Displays Simple Graphs of data', action = 'store_true')
        argParser.add_argument("--csv", help = 'Stores recorded data as a CSV', action = 'store_true')
        return argParser

    def makeWordCloud(self):
        plots = len(self.users)
        cols = np.ceil(np.sqrt(plots))
        rows = np.ceil(plots/cols)
        i = 1
        plt.figure(figsize = (cols*5,rows*5), facecolor = '#f5f5f5')
        
        for user in self.users:
            words = self.users.get(user)[3]
            if len(words) == 0:
                continue
            words = words.lower()

            wordcloud = WordCloud(width = 800, height = 800,
            background_color ='#f5f5f5',
            stopwords = set(STOPWORDS),
            min_font_size = 1).generate(words)

            plt.subplot(int(rows),int(cols),i).set_title(user, fontweight = 'bold')
            plt.imshow(wordcloud)
            plt.axis("off")
            plt.tight_layout(pad = 1)
            i+=1
        plt.savefig('gitStatWordCloud.png')

    def makeCSV(self):
        fields = ["User Name", "Additions", "Deletions", "Commits", "Start Date", "Commits per Weekday"]
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
                row+=[userStats[4]]#Start Date
                row+=[userStats[5]]#Commits Per Weekday
                outputWriter.writerow(row)
        return
    def grantAwards(self):
        ##Award List
        #Most Sporadic Committer
        #Prolific Puller
        #Weekend Warrior
        #
        return
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
            plt.xticks(rotation = 90)
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
        if self.args.addr:
            if "." in self.args.addr:
                if self.args.addr.split(".")[1] == "csv":
                    try:
                        with open(self.args.addr) as csvInput:
                            inputReader = csv.reader(csvInput)
                            for row in inputReader:
                                repos+=row     
                    except FileNotFoundError:
                        print("Indicated CSV does not exist")
                else:
                    repos = os.listdir(self.args.addr)
            else:
                repos = os.listdir(self.args.addr)
        else:
            repos = os.listdir(os.curdir)
        if self.args.repos:
            repos += self.args.repos.split(",")

        #Load List of Repository Owners
        owners = self.args.owners.split(',')

        for repo in repos:
            for owner in owners:

                params = {"repo":repo,"owner":owner}
                response = self.session.post(self.url,json={'query':queryBase, 'variables':params})
                data = json.loads(response.text)
                data = data["data"]["repository"]

                if not data:
                    continue

                data = data["ref"]["target"]["history"]["edges"]
                for commit in data:
                    commit = commit['node']
                    author = commit["author"]["name"]
                    date = commit["author"]["date"]
                    commitMessage = commit["message"]
                    additions = commit["additions"]
                    deletions = commit["deletions"]

                    date = date.split("T")[0].split("-")
                    weekdayCheck = datetime.date(int(date[0]),int(date[1]),int(date[2]))
                    weekdayCheck = weekdayCheck.weekday()

                    if author not in self.users:
                        weekdayCommitCount = [0,0,0,0,0,0,0]
                        weekdayCommitCount[weekdayCheck]+=1
                        commits = 1
                        startDate = date
                        self.users[author] = [additions, deletions,commits,commitMessage,startDate, weekdayCommitCount]
                    else:
                        user = self.users.get(author)
                        additions += user[0]
                        deletions += user[1]
                        commits += user[2]
                        commitMessage += user[3]
                        weekendCommit = user[5]
                        weekendCommit[weekdayCheck]+=1
                        startDate = date
                        self.users[author] = [additions, deletions,commits,commitMessage,date, weekdayCommitCount]
    def execute(self):
        self.getStats()
        if self.args.wordCloud:
            self.makeWordCloud()
        if self.args.graphStats:
            self.graphStats()
        if self.args.csv:
            self.makeCSV()
if __name__ == "__main__":
    engine = gitStatistics(sys.argv[1:])
    engine.execute()
