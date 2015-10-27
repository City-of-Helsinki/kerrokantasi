
# User profile

# Groups
 1. official
 2. resident
 3. anonymous (if required)
 
# Languages (Could be hardcoded instead of db model. There are only three anyway.)

# CommonModel
 - uuid
 - created
 - updated
 - deleted flag
 - author (nullable) ?

# Hearing 
 - closing time
 - number of comments
 (avoid selects from comments, to count them by hearing, update hearing when commented)
 - location
 - status (open/closed flag)
 - heading
 - abstract
 - content
 - borough
 - comments enabled
 - author

Translation is done with django-modeltranslation.
http://django-modeltranslation.readthedocs.org

# HearingLabels
 - hearing FK
 - label

# Report (model or computed from data?)

# CommonComment
 - author
 - time
 - likes (again, keep number of likes instead of counting them all the time)
 - comment
 - language

## HearingComment
  - hearing FK

## ScenarioComment
  - scenario FK

# ServiceComment
 - email
 - firstname, lastname
 - title

# CommentHistory
 - datetime
 - content
 - author

# CommonLike
 - user FK

## HearingLike
 - hearing FK

## CommentLike
 - comment FK
 
# CommonFollower
 - user FK
 
## CommentFollower
 - comment FK

## HearingFollower
 - hearing FK

# Scenario
 - hearing FK
 - abstract
 - content

# Introduction
 - hearing FK
 - abstract
 - content

# Processing
 - hearing FK

# ProcessingStep
 - Processing FK

# CommonImage
 - type (original, small, thumbnail)
 - title
 - caption
 - ulr/location
 - height
 - width

If multiple captions per image are required, we need CaptionImage model.

## HearingImage
  - hearing FK

## ScenarioImage
  - scenario FK

## IntroductionImage
  - introduction FK

