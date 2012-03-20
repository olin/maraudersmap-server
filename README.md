# Marauder's map

Marauder's map helps students see where other students are on Olin's campus.

This is the start of an attempt to modernize **The Marauder's Map @ Olin**, 
an application written between 2008 and 2010 by Andrew Barry and Ben Fischer.
It used wxPython, PHP, and MySQL.

This repository is for *server* development. For client development, see 
[https://github.com/ohack/maraudersmap-client/](Marauder's Map Client Repository).

## About the Server

The original server stack was written in PHP and MySQL. We are attempting to improve and modernize it, 
using Python, a simple microframework, [Flask](http://flask.pocoo.org/), and likely MySQL, or perhaps MongoDB, 
depending on pending design decisions.

In addressing some of the issues of the previous version of *Marauder's Map @ Olin*, we will strive for

### Maintainability

* Code will be legibile, compliant with [PEP8](http://www.python.org/dev/peps/pep-0008/),
and commented (using the [Sphinx .rst markup syntax](sphinx.pocoo.org))
* Code will have tests to document its status 
(using the [Python unittesting framework](http://docs.python.org/library/unittest.html))
* The actual project will be documented in a way such that it can be extended, replicated,
and/or restarted relatively easily

### Educational value:

* Standards and standard libraries will be leveraged where available, i.e. JSON for communication general good practices
* Made open and involve as many students as possible; perhaps it can be leveraged in future applications?