# PlayerbaseAnalysis

# The Impact of Updates on Game Popularity


## Objective
This project will investigate whether major updates and DLC releases cause noticeable changes in the popularity of popular Steam games. Approximately five games will be selected, with three major updates or DLC releases identified for each, and player counts before and after these events will be compared to identify common patterns.

## Motivation
	Looking into the effects of updates on player count would provide insight into overall retention in a game’s popularity. This data could then be used in future projects to determine the effectiveness of rolling out larger updates and content changes rather than a lot of smaller changes. The data would also provide insight into what practices game developers are using to make games that are dying out popular again. All of the data will also further support business cases that companies will be making. For example, if the results show that larger updates have a bigger impact on game popularity then they will be more likely to keep a larger team of developers that work on projects that get released every couple of quarters.

## Data
Historical player-count data will be obtained from SteamCharts or similar publicly available sources, while update and DLC information will be collected from the Steam Web API and Steam store pages. The biggest challenge that we are expecting to run into is the initial collection of the data, then the data using different formats. We are also going to be mindful that the data will not tell the whole story as there are other factors that could affect a game’s popularity, such as popularity on streaming sites like Twitch or YouTube. 

## Approach
The data will be retrieved using the method covered in the Data section, cleaned to a single format, and combined using Python before analyzing changes in player counts. Python will be the biggest tool throughout this project as it will be used in pulling the data using the APIs, cleaning the output of our data into a consistent format, and generating tables that can be used for analysis and in the final presentation/write-up. Specific libraries that we will be using will include requests for the initial pull of the data, Pandas for data cleaning, and Matplotlib for data visualization.

## Team Responsibilities
### Andrew Berard: 
Andrew will pull the historical player-count data for the chosen games that are focused on. Then Andrew will normalize the data into a consistent format that can be used to generate graphs that will be used during the project’s analysis.

### Kaden Bissonnette:
Kaden analyzes the data that was collected throughout the first stages of the project to determine the effects that DLCs or large updates have on a game’s popularity with Jubin. Kaden will then add this analysis to the report and import the figures that have been generated throughout the project to support the findings.

### Perry Shu:
	Perry will gather the update and DLC information for the games that are focused on for this project. Then Perry will normalize the collected data into a consistent format that can be used to compare the data that Andrew normalized so the data can be used in the analysis of the project.

### Jubin Jaydeep Vijayakumar:
	Jubin will analyze the data that was collected throughout the first stages of the project and determine the effects of DLCs and larger updates on a game’s popularity with Kaden. Then Jubin will generate the presentation slides using the figures and data generated throughout the project to support the claims the team makes.

## Timeline and Milestones
The major steps to complete the project are the two pieces of data collection followed by the analysis of the data. The data will be collected from two sources, Steam API and SteamCharts. Both sources contain different data that the other would not have,  and are necessary for the completion of the project. Steam API will provide historical player-count data for the games we choose to focus on. SteamCharts will provide  update and DLC information for the same games. The resulting data from both will be normalized and stored in csvs. The data analysis will make help compare the two pieces of data for each game, helping track the player-base at the time of a given major event in a game. Then questions can be answered and created and interpretations of the data can occur. 
A possible timeline would be as follows, with expected deliverables to check progress:
Week 1: select ten games, create code to pull data
Deliverable: at least two csvs of data, at least two notebooks or Python scripts that pull data
Started by Oct. 27, finished by Nov. 3
Week 2: process data with pandas, Establish patterns
Deliverable: completed notebooks analyzing data. Should include graphs and tables comparing and grouping data
Started by Nov. 3, finished by Nov. 10
Week 3: interpret results, compare data, make presentation. 
Deliverable: presentation, final report
Presentation finished by presentation day, report finished by Dec. 1

## Expected Outcome
The expected outcome for this project is a data analysis that can show whether major updates and DLC releases cause notable changes in popularity of popular Steam games. For each of the games, player counts before and after major releases will be compared to identify common patterns. The results will be presented as tables and Matplotlib visualizations, along with summaries of the trends we found. We expect that updates and DLC releases will usually be followed up with a short-term increase in player counts, and our overall analysis will look at how long that increase lasts. If a larger DLC has a bigger impact, this would support a business argument where keeping larger teams of developers working on bigger content drops would be reasonable. Little to no changes would also be a useful finding, since it suggests that other factors matter more. Since player counts do not explain the full story, limitations that we cannot take into account like sudden popularity on content platforms like YouTube and Twitch will be noted in the final write-up and presentation.
