
# API endpoints

Language used as GET parameter anywhere

## /notifications

 - send #26

## /account
 
 - register #9
 - update user info #11

## /api/v1/hearing/

List hearings, get detail. Anonymous access.

 - **get next closing hearings** #1 _/api/v1/hearing/<hearingID>/?nextclosing_
 - **list all** #4 _/api/v1/hearing/_
 - **search/filter** #5 _/api/v1/hearing/<hearingID>/?filter=foo&search=bar_
 - **order** #6 _/api/v1/hearing/?orderby=<foo>_
 - **get location** #7 _/api/v1/hearing/<hearingID>/_
 - **get detail** #8 _/api/v1/hearing/<hearingID>/_
 - **top hearings** #2 _/api/v1/hearing/?newest=N_

## /api/v1/hearing/

List hearings. Get detail. Create, update, delete. Authenticated user at _/api/v1/hearing/<hearingID>/_ :

 - **list all by owner** #15 _/api/v1/hearing/?createdby=<userID>_
 - **CRUD** #15
 - **disable/enable comments** #16
 - **set map** #17
 - **set commenting options** #22

## /api/v1/labels/

List labels. Get detail. Create, update.

 - **list** _/api/v1/labels/?hearing=<hearingID>_
 - **CRUD** #23 _/api/v1/labels/<labelID>_

## /api/v1/reports/

List reports. Get detail.

 - **top reports** _/api/v1/reports/?newest=N_
 - **get report** #24 _/api/v1/reports/<hearingID>_

## /api/v1/follow/

Follow hearing or comment.

 - **follow hearing** #10 _/api/v1/follow/?follower=<userID>&type=hearing&id=<hearingID>_
 - **follow comment** #10 _/api/v1/follow/?follower=<userID>&type=comment&id=<commentID>_

## /api/v1/images/

List images. Get detail. Create, update, delete.

 - **add image to hearing** #18 _/api/v1/images/?hearing=<hearingID>_
 - **add image to scenario** #40 _/api/v1/images/?scenario=<scenarioID>_
 - **add image to introduction** #40 _/api/v1/images/?introduction=<introductionID>_
 - **CRUD** #18 _/api/v1/images/<imageID>_
 - **list all added to hearing** #37 _/api/v1/images/?hearing=<hearingID>_
 - **list all added to scenario**  _/api/v1/images/?scenario=<scenarioID>_
 - **list all added to introduction** _/api/v1/images/?introduction=<introductionID>_

## /api/v1/scenario/

List scenarios. Get detail. Create, update, delete.

 - **list all scenarios added to hearing** #21 _/api/v1/scenario/?hearing=<hearingID>_
 - **add scenario to hearing** #21 _/api/v1/scenario/?hearing=<hearingID>_
 - **get detail about scenario** #21 _/api/v1/scenario/<scenarioID>_
 - **update and delete scenario** #25 _/api/v1/scenario/<scenarioID>_

## /api/v1/introduction/

List introductions. Get detail. Create, update, delete.

 - **list all introductions added to hearing** #25 _/api/v1/introduction/?hearing=<hearingID>_
 - **add introduction to hearing** #25 _/api/v1/introduction/?hearing=<hearingID>_
 - **get detail about introduction** #25 _/api/v1/introduction/<introductionID>_
 - **update and delete introduction** #25 _/api/v1/introduction/<introductionID>_

## /api/v1/comments/

List comments. Add comments. Vote. Update or delete.

 - **add comment to hearing** #28 _/api/v1/comments/?hearing=<hearingID>_
 - **list comments of a hearing** #28 _/api/v1/comments/?hearing=<hearingID>_
 - **add comment to scenario** #27 _/api/v1/comments/?scenario=<scenarioID>_
 - **list comments of a scenario** #27 _/api/v1/comments/?scenario=<scenarioID>_
 - **add a vote** #31 _/api/v1/comments/<commentID>?vote=<userID>_
 - **get detail (with number of comments)** _/api/v1/comments/<commentID>_
 - **Update, delete** _/api/v1/comments/<commentID>_

## TODO:

### /hearing/processing

### /hearing/processing/step

 - list #20
 - get detail #20

### /comment/hearing/top

 - top actively commented hearings #3

### /comment/service

 - add comments about service itself #35

