

# General rules

Translation is done with django-modeltranslation.
http://django-modeltranslation.readthedocs.org

List of available languages can be builtin instead of database model.
(We provide only three languages anyway)

# User profile

# Groups
 1. official
 2. resident
 3. anonymous (if required)

# Processing (CommonModel)

**Model for processing.**

 - **hearing** - _a reference to hearing (FK)_

# ProcessingStep (CommonModel)

**Model for processing steps.**

 - **processing** - _a reference to processing (FK)_
