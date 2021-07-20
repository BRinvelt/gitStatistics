# gitStatistics
A tool for recording repository commit statistics and extracting interesting information.

Uses version 4 of the [GitHub API](https://docs.github.com/en/graphql)
# Usage
```python3 gitStatistics.py apiKey owners (Optional Args)```

This command attempts to execute the script on any repositories located within the current directory

*apiKey* is your *github apiKey*, and *owners* is a *comma separated list of the owners of targetted repositories*

## Optional Arguments
- --branch, --b: User defined target branch, default is master
- --hostname, --hn: https://user-specified-hostname/api/graphql - use for enterprise GitHubs
- --repos, --r: Additional Repos to analyze - Comma separated repo(s)
- --excludeRepos, --er: Comma separated repo(s) to exclude
- --addr: Address of a folder containing repos or csv containing repo names
- --wordCloud, --wc: Generate word clouds from commit messages
- --graphStats, --gs: Create Simple Graphs of data
- --csv: Stores key recorded data as a CSV
- --awards, --aw: Prints awards/titles for users based on their statistics
- --startTime, --st: Earliest commit time since epoch to accept (seconds)
- --endTime, --et: Latest commit time since epoch to accept (seconds)
