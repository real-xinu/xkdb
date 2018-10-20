[![Build Status](https://travis-ci.org/ammaraskar/xkdb.svg?branch=master)](https://travis-ci.org/ammaraskar/xkdb)
[![Code Coverage](https://codecov.io/gh/ammaraskar/xkdb/branch/master/graph/badge.svg)](https://codecov.io/gh/ammaraskar/xkdb)
# xkdb
Xinu Kernel DeBugger

## Project Structure

* `stub/` - The gdb stub and changes on the Xinu side to act as
  a remote debugging target.

* `py-console/` - A Python version of the `cs-console` command,
  used to establish a connection to the Xinu backends and pipe
  data in and out through to GDB.

## Running Tests

`cd py-console`

`python -m pytest`
