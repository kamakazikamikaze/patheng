# Pathway Engineering's Python Toolkit

## The key to awesome automation

The `patheng` package is a collection of modules and functions that many of our scripts use. Rather than copy-paste blocks of code in each script that have to be manually updated when blowing the dust off of them, they are instead centralized and updated in one location to keep everything unified. Spaghetti code and monkey-patches are no longer allowed in this environment: structure is mandatory and maintainability is an absolute must!

## What does/will this contain?

* ElasticSearch handlers
  * Setting up indices
  * Bulk-pushes to clusters
  * Offloading when clusters aren't reachable
* General utilities
  * Reading in configuration files and minimum field requirements
  * Ping-checks if hosts are alive
  * Simple line-by-line loading of file to a list


### To-Do

* General utilities
  * Report creation
* Cisco handlers
  * Device configuration modification
  * Autoprovisioning
  

## License

Copyright (C) Brigham Young University Office of IT, Infrastructure Services – Pathway Engineering Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.