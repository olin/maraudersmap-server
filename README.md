# Marauder's map

Marauder's map helps students see where other students are on Olin's campus.

This is the start of an attempt to modernize *Marauder's Map @ Olin*, an application written between 2008 and 2010 by Andrew Barry and Ben Fischer, which used wxPython, PHP, and MySQL.

This repository is for *server* development, for client development, see [https://github.com/ohack/maraudersmap-client/](Marauder's Map-client)

The original server stack was written in php and mysql. We are attempting to improve it and modernize it, using Python and a simple microframework, [Flask](http://flask.pocoo.org/), and likely MySQL, or perhaps MongoDB, depending on pending design decisions.

In addressing some of the issues of the previous version of *Marauder's Map @ Olin*, we will strive for

## Maintainability

* Code will be legibile and at commented
* Code will have tests to document its status
* The actual project will be documented in a way such that it can be replicated and or restarted relatively easily

## Educational value:

* Standards and standard libraries will be leveraged where available, i.e. JSON for communication general good practices
* Made open and involve as many students as possible, perhaps it can be leveraged in future applications?