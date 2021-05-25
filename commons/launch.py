class AnalysisResult:
    def __init__(self, testItem, issueType, relevantItem):
        self.testItem = testItem
        self.issueType = issueType
        self.relevantItem = relevantItem

    def __str__(self):
        return "Test item: {}; Issue type: {}; Relevant test item: {}".format(
            self.testItem, self.issueType, self.relevantItem
        )


class SearchConfig:
    def __init__(
            self, searchLogsMinShouldMatch, minDocFreq, minTermFreq, minShouldMatch,
            boostUniqueId=2.0, boostAA=2.0, boostLaunch=2.0
    ):
        self.searchLogsMinShouldMatch = searchLogsMinShouldMatch
        self.minDocFreq = minDocFreq
        self.minTermFreq = minTermFreq
        self.minShouldMatch = minShouldMatch
        self.boostUniqueId = boostUniqueId
        self.boostAA = boostAA
        self.boostLaunch = boostLaunch


class SearchLogs:
    def __init__(self, launchId, launchName, itemId, projectId, filteredLaunchIds, logMessages, loglines):
        self.launchId = launchId
        self.launchName = launchName
        self.itemId = itemId
        self.projectId = projectId
        self.filteredLaunchIds = filteredLaunchIds
        self.logMessages = logMessages
        self.loglines = loglines


class Config:
    def __init__(
            self, logLines, minDocFreq=0, minTermFreq=0, minShouldMatch=0, mode="SearchModeAll"
    ):
        self.numberOfLogLines = logLines
        self.analyzerMode = mode
        self.minDocFreq = minDocFreq
        self.minTermFreq = minTermFreq
        self.minShouldMatch = minShouldMatch


class Log:
    def __init__(self, logId, logLevel, message, logTime):
        self.logId = logId
        self.logLevel = logLevel
        self.message = message
        self.logTime = logTime

    def __str__(self):
        return "Log Id: {}; LogLevel: {}; Log time: {};\nLog message: {}".format(
            self.logId, self.logLevel, self.logTime, self.message
        )


class TestItem:
    def __init__(
            self, testItemId, uniqueId, name, description, isAutoAnalyzed, issueType,
            issueDescription, links_to_bts, originalIssueType, startTime, endTime,
            lastModified, logs
    ):
        self.testItemId = testItemId
        self.uniqueId = uniqueId
        self.name = name
        self.isAutoAnalyzed = isAutoAnalyzed
        self.issueType = issueType
        self.description = description
        self.issueDescription = issueDescription
        self.links_to_bts = links_to_bts
        self.originalIssueType = originalIssueType
        self.logs = logs
        self.startTime = startTime
        self.endTime = endTime
        self.lastModified = lastModified

    def __str__(self):
        return """Test item Id: {}; UniqueId: {}; Name: {}; Item Description {}; Auto analyzed: {};" \
                IssueType: {} Issue Description: {} Links to BTS: {} Start time {}""".format(
            self.testItemId, self.uniqueId, self.name,
            self.description, self.isAutoAnalyzed, self.issueType,
            self.issueDescription, self.links_to_bts, self.startTime
        )


class Launch:
    def __init__(
            self, launchId, project, launchName, description, analyzerConfig,
            statistics, startTime, endTime, lastModified, number, testItems
    ):
        self.launchId = launchId
        self.project = project
        self.launchName = launchName
        self.description = description
        self.analyzerConfig = analyzerConfig
        self.testItems = testItems
        self.statistics = statistics
        self.startTime = startTime
        self.endTime = endTime
        self.lastModified = lastModified
        self.number = number


class Project:
    def __init__(self, projectId, configuration, launches):
        self.projectId = projectId
        self.configuration = configuration
        self.launches = launches


class SearchLogsRequest:
    def __init__(self, project, testItemId, analyzerConfig, logMessages):
        self.project = project
        self.testItemId = testItemId
        self.analyzerConfig = analyzerConfig
        self.logMessages = logMessages
