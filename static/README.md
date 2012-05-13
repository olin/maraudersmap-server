# Marauder's map

Marauder's map helps students see where other students are on Olin's campus.

This is the start of an attempt to modernize **The Marauder's Map @ Olin**, 
an application written between 2008 and 2010 by Andrew Barry and Ben Fischer.
It used wxPython, PHP, and MySQL.

This repository is for *server* development. For client development, see 
[https://github.com/ohack/maraudersmap-client/](Marauder's Map Client Repository).

## About the UI

The original web interface was written in custom javascript and presented via php. We are modernizing it 
with a full redesign that uses a JSON interface for API calls. Since the javascript API is open, it will 
be possible for 3rd parties to create custom plugins and unique location-enabled web applications.

In addressing some of the issues of the previous version of *Marauder's Map @ Olin*, we will strive for

### Maintainability

* Code will be legibile and commented (using the [Sphinx .rst markup syntax](sphinx.pocoo.org))
* Code will have tests to document its status 
* The actual project will be documented in a way such that it can be extended, replicated,
and/or restarted relatively easily

### Educational value:

* Standards and standard libraries will be leveraged where available, i.e. JSON for communication general good practices
* Made open and involve as many students as possible; perhaps it can be leveraged in future applications?



### When first running locally, do:

    sudo pip install virtualenv
    sudo virtualenv venv --distribute
    source venv/bin/activate
    sudo pip install -r requirements.txt

### Then every time locally running:

    source venv/bin/activate
