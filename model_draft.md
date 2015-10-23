
# User profile

# Groups
 1. official
 2. resident
 3. anonymous (if required)
 
# Languages (Could be hardcoded instead of db model. There are only three anyway.)

# Hearing 
 - closing time
 - number of comments
 (avoid selects from comments, to count them by hearing, update hearing when commented)
 - location
 - status
 - content
 - borough
 - comments enabled
 - author

## HearingTranslation

Translated content could be fetched after hearing has been fetched and then merged before payload is generated.

 - hearing FK
 - content
 - lang code


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
 - content

# Introduction
 - hearing FK
 - content

# Processing
 - hearing FK

# ProcessingStep
 - Processing FK

# CommonImage

## HearingImage
  - hearing FK

## ScenarioImage
  - scenario FK

## IntroductionImage
  - introduction FK

