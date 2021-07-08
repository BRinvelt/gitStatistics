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
##TODO:Add Comments throughout / rationalize code to improve legibility and usability
queryBase = """
query($repo: String!, $owner: String!)
{
    repository(name: $repo, owner: $owner){
        pullRequests(first:100){
            nodes{
                author{
                    login
                }
                merged
                closed
                commits(last:100){
                    nodes{
                        commit{
                            deletions
                            additions
                            committedDate
                            message
                        }
                    }
                }
            }
            edges {
                cursor
            }
        }

    }
}
"""

queryRepeat = """
query($repo: String!, $owner: String!, $cursor: String!)
{
    repository(name: $repo, owner: $owner){
        pullRequests(first:100, after: $cursor){
            nodes{
                author{
                    login
                }
                merged
                closed
                commits(last:100){
                    nodes{
                        commit{
                            deletions
                            additions
                            committedDate
                            message
                        }
                    }
                }
            }
            edges {
                cursor
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
        #Set a default base URL for api calls
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
            words = self.users.get(user)[6]
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
        plt.savefig('wordCloud.png')

    def makeCSV(self):
        fields = ["User Name", "Additions", "Deletions","Pull Requests", "Commits", "Merged Requests", "Closed Requests", "Weekend Commits", "Start Date"]
        with open('gitStatistics.csv', 'w') as csvOutput:
            outputWriter = csv.writer(csvOutput)
            outputWriter.writerow(fields)
            for user in self.users:
                userStats = self.users.get(user)
                row = [user]
                row+=[userStats[0]]
                row+=[userStats[1]]
                row+=[userStats[2]]
                row+=[userStats[3]]
                row+=[userStats[4]]
                row+=[userStats[5]]
                row+=[userStats[7]]
                row+=[userStats[8]]
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
        #Graph General Data
        additionBar=[] #0
        deletionBar=[] #1
        pullBar=[] #2
        mergeBar=[] #4
        closeBar=[] #5
        
        for user in self.users:
            additionBar.append(self.users.get(user)[0])
            deletionBar.append(self.users.get(user)[1])
            pullBar.append(self.users.get(user)[2])
            mergeBar.append(self.users.get(user)[4])
            closeBar.append(self.users.get(user)[5])

        with PdfPages('multipage_pdf.pdf') as pdf:
            #Report Addition and Deletion Statistics
            barWidth = .25
            br1 = np.arange(len(additionBar))
            br2 = [x + barWidth for x in br1]
            figAddDel = plt.subplots(figsize = (12,10), facecolor = '#f5f5f5')
            plt.bar(br1,additionBar,width=barWidth,color = '#6cc644',label = 'Total Additions')
            plt.bar(br2,deletionBar,width=barWidth, color ='#bd2c00',label = 'Total Deletions')
            plt.xticks([r+barWidth/2 for r in range(len(additionBar))],self.users)
            plt.xticks(rotation = 90)
            plt.title("Commit Additions and Deletions", fontweight = 'bold')
            plt.legend()
            pdf.savefig()

            #Report Pull Request Outcomes
            barWidth = .25
            br1 = np.arange(len(additionBar))
            br2 = [x + barWidth for x in br1]
            br3 = [x + barWidth for x in br2]
            figPMC = plt.subplots(figsize = (12,10), facecolor = '#f5f5f5')
            plt.bar(br1,pullBar,width=barWidth, color = '#4078c0',label = 'Pull Requests')
            plt.bar(br2,mergeBar,width=barWidth, color ='#6cc644',label = 'Merged Requests')
            plt.bar(br3,closeBar,width=barWidth, color ='#bd2c00',label = 'Closed (unmerged) Requests')
            plt.xticks([r + barWidth for r in range(len(additionBar))],self.users)
            plt.xticks(rotation = 90)
            plt.title("Pull Request Outcomes", fontweight = 'bold')
            plt.legend()
            pdf.savefig()

            #Report Daily Commits
            dayNames = ["Mon","Tue","Wed","Thur","Fri","Sat","Sun"]
            figDaily = plt.figure(figsize = (12,10), facecolor = '#f5f5f5')
            plt.bar(dayNames,self.dayOfWeek, color = '#4078c0',)
            plt.title("Commits per day of Week", fontweight = 'bold')
            userWW = None
            for user in self.users:
                if userWW == None:
                    if self.users.get(user)[7]>0:
                        userWW = user
                else:
                    if self.users.get(userWW)[7] < self.users.get(user)[7]:
                        userWW = user
            if userWW != None:
                plt.xlabel("Weekend Warrior: "+ userWW +" made the most Weekend Commits", fontweight = 'bold')
            plt.ylabel("Number of Commits")
            pdf.savefig()
        #Give Awards
        return

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
        #Initialize Dictionary for Key Users and stats

        for repo in repos:
            for owner in owners:

                params = {"repo":repo,"owner":owner}
                response = self.session.post(self.url,json={'query':queryBase, 'variables':params})
                while True:
                    data = json.loads(response.text)
                    data = data["data"]["repository"]

                    if not data:
                        break

                    for cursor in data["pullRequests"]["edges"]:
                        lastCursor = cursor.get("cursor")

                    pullCount = len(data["pullRequests"]["nodes"])
                    data = data["pullRequests"]["nodes"]
                    for pullRequest in data:
                        author = pullRequest["author"]["login"]
                        merged = pullRequest["merged"]
                        if not merged:
                            closed = pullRequest["closed"]
                        else:
                            closed = False

                        pullRequest = pullRequest["commits"]["nodes"]
                        additions = 0
                        deletions = 0
                        commits = 0
                        commitText = ""
                        weekendCommit = 0
                        startDate = None

                        for commit in pullRequest:
                            commit = commit["commit"]
                            additions += commit["additions"]
                            deletions += commit["deletions"]
                            commits += 1
                            commitText += (commit["message"]+" ").replace("\n"," ")

                            commitDate = commit["committedDate"]
                            commitDate = commitDate.split("T")[0].split("-")
                            commitDate = datetime.date(int(commitDate[0]),int(commitDate[1]),int(commitDate[2]))
                            if startDate is None:
                                startDate = commitDate
                            commitDate = commitDate.weekday()
                            self.dayOfWeek[commitDate]+=1
                            if commitDate > 4:
                                weekendCommit+=1

                        if author not in self.users:
                            self.users[author] = [additions, deletions,1,commits,int(merged),int(closed),commitText,weekendCommit,startDate]
                        else:
                            user = self.users.get(author)
                            additions += user[0]
                            deletions += user[1]
                            pullRequestCount = user[2]+1
                            commits += user[3]
                            merges = int(merged) + user[4]
                            closes = int(closed) + user[5]
                            commitText += user[6]
                            weekendCommit += user[7]
                            startDate = user[8]
                            self.users[author] = [additions, deletions,pullRequestCount,commits,merges,closes,commitText,weekendCommit,startDate]
                    if pullCount == 100:
                        params = {"repo":repo,"owner":owner,"cursor":str(lastCursor)}
                        response = requests.post(self.url,json={'query':queryRepeat, 'variables':params})
                    else:
                        break
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
