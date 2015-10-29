
# API endpoints

Language used as GET parameter anywhere

## /notifications

 - send #26

## /account
 
 - register #9
 - update user info #11

## Hearings

### /api/v1/hearing/

List hearings, get detail. Anonymous access.

 - **get next closing hearings** #1 _/api/v1/hearing/<hearingID>/?nextclosing_
 - **list all** #4 _/api/v1/hearing/_
 - **search/filter** #5 _/api/v1/hearing/<hearingID>/?filter=foo&search=bar_
 - **order** #6 _/api/v1/hearing/?orderby=<foo>_
 - **get location** #7 _/api/v1/hearing/<hearingID>/_
 - **get detail** #8 _/api/v1/hearing/<hearingID>/_
 - **top hearings** #2 _/api/v1/hearing/?newest=N_

List comments, introductions, scenarios, images.

 - **list all comments added to hearing** #28 _/api/v1/hearing/<hearingID>/comments/_
 - **list all introductions added to hearing** #25 _/api/v1/hearing/<hearingID>/introductions/_
 - **list all images added to hearing** #37 _/api/v1/hearing/<hearingID>/images/_
 - **list all scenarios added to hearing** #21 _/api/v1/<hearingID>/scenarios_

Add comment, introduction, scenario, image.

 - **add comment to hearing** #28 _/api/v1/hearing/<hearingID>/comment/_
 - **add introduction to hearing** #25 _/api/v1/hearing/<hearingID>/introduction/_
 - **add scenario to hearing** #21 _/api/v1/hearing/<hearingID>/scenario/_
 - **add image to hearing** #18 _/api/v1/hearing/<hearingID>/image/_

Follow hearing.

 - **add follower to a hearing** #10 _/api/v1/hearing/<hearingID>/follow/?follower=<userID>_

### /api/v1/hearing/

List hearings. Get detail. Create, update, delete. Authenticated user at _/api/v1/hearing/<hearingID>/_ :

 - **list all by owner** #15 _/api/v1/hearing/?createdby=<userID>_
 - **CRUD** #15
 - **disable/enable comments** #16
 - **set map** #17
 - **set commenting options** #22

## Reports

### /api/v1/reports/

List reports. Get detail.

 - **top reports** _/api/v1/reports/?newest=N_
 - **get report** #24 _/api/v1/reports/<hearingID>_

## Images

### /api/v1/images/

Get detail. Update, delete.

 - **Get detail. Update, delete** #18 _/api/v1/images/<imageID>_

## Scenarios

### /api/v1/scenario/

Get detail. Update, delete.

 - **get detail about scenario** #21 _/api/v1/scenario/<scenarioID>_
 - **update and delete scenario** #25 _/api/v1/scenario/<scenarioID>_

List images, comments.

 - **list all added to scenario**  _/api/v1/scenario/<scenarioID>/images/_
 - **list comments of a scenario** #27 _/api/v1/scenario/<scenarioID>/comments/_

Add image, comment.

 - **add image to scenario** #40 _/api/v1/scenario/<scenarioID>/image/_
 - **add comment to scenario** #27 _/api/v1/scenario/<scenarioID>/comment/_

## Introductions

### /api/v1/introduction/

Get detail. Update, delete.

 - **get detail about introduction** #25 _/api/v1/introduction/<introductionID>_
 - **update and delete introduction** #25 _/api/v1/introduction/<introductionID>_

List images.

 - **list all added to introduction** _/api/v1/introduction/<introductionID>/images/_

Add image.

 - **add image to introduction** #40 _/api/v1/introduction/<introductionID>/image/_

## Comments

### /api/v1/comments/

Vote. Update or delete.

 - **add a vote** #31 _/api/v1/comments/<commentID>/vote/?voter=<userID>_
 - **get detail (with number of comments)** _/api/v1/comments/<commentID>_
 - **Update, delete** _/api/v1/comments/<commentID>_

Follow comment.

 - **add follower** #10 _/api/v1/comments/<commentID>/follow/?follower=<userID>_

## TODO:

### /hearing/processing

### /hearing/processing/step

 - list #20
 - get detail #20

### /comment/hearing/top

 - top actively commented hearings #3

### /comment/service

 - add comments about service itself #35

## /api/v1/labels/

List labels. Get detail. Create, update.

 - **list** _/api/v1/labels/?hearing=<hearingID>_
 - **CRUD** #23 _/api/v1/labels/<labelID>_

