# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

A community based platform to publish users' urban walking trails, building a network for sharing information and advice between casual explorers and hobbyists

## User stories

### As a hobbyist
- I want to publish a new walking trail with a title and description so that I can share my favorite routes with the community.
- I want to search for trails by neighborhood or keyword so that I can find routes in specific areas I plan to explore.
- I want to view the full details of a specific trail, including its duration and difficulty, so that I can decide if it fits my schedule and ability.
- I want to edit the information of a trail I previously uploaded so that I can keep the route details accurate and up-to-date.
- I want to delete a trail I created so that I can remove duplicate entries or routes that are no longer accessible.

### As a casual explorer
- I want to browse a list of all registered trails so that I can spontaneously choose a route to explore.
- I want to search for trails by difficulty level so that I can find a walk that matches my energy level.
- I want to view the estimated duration of a trail so that I can plan my day effectively.
- I want to see the starting point of a trail so that I can easily navigate to the beginning of the route.
- I want to read descriptions of the scenery so that I can choose a trail that offers the visual experience I am looking for.

### As an experienced hiker
- I want to publish my completed hikes with maps, stats, and photos so that others can see my routes and achievements.
- I want to browse hikes shared by other hikers so that I can discover new and challenging trails.
- I want to follow other hikers so that I can stay updated on their latest adventures.
- I want to like and comment on other people’s hikes so that I can engage with the hiking community.
- I want to compare my hike statistics (distance, elevation gain, pace) with others who completed the same trail so that I can benchmark my performance.

### As a moderator
- I want to regulate published hikes to the app, so that inappropiate content is not seen by users
- I want to warn users, so that if users know what rules they may be violating and steps they can take to avoid repeat offenses
- I want to suspend or ban users, so that any users who are disrupting the experience for others do not continue to do so
- I want to alert users on their posts, so that any incorrect data on hikes can be corrected for greater accuracy
- I want to talk to the community, so that any complaints can potentially be passed up to the developers of the app


## Steps necessary to run the software
*Windows*
```
$ python -m venv venv 
$ .\venv\Scripts\activate
$ pip install -r requirements.txt
$ python app.py
```

*MacOS*
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Task boards

https://github.com/orgs/swe-students-spring2026/projects/44/views/2
