[![Build Status](https://travis-ci.org/ammaraskar/xkdb.svg?branch=master)](https://travis-ci.org/ammaraskar/xkdb)
[![Code Coverage](https://codecov.io/gh/ammaraskar/xkdb/branch/master/graph/badge.svg)](https://codecov.io/gh/ammaraskar/xkdb)
# xkdb
Xinu Kernel DeBugger

## How to Use

## Project Structure

* `stub/` - The gdb stub and changes on the Xinu side to act as
  a remote debugging target.

* `py-console/` - A Python version of the `cs-console` command,
  used to establish a connection to the Xinu backends and pipe
  data in and out through to GDB.

## Running Tests

`cd py-console`

`python -m pytest`

## How does it work?

This project leverages the ability of GDB to debug remote targets using a thin
text protocol. The primary purpose of this protocol is to allow the use of GDB 
on systems where compiling the full debugger is too difficult. A remote host
can then drive the debugging session by sending simple commands to the small
gdb server. 

By equipping a board running Xinu with the GDB stub, we allow a remote host 
running GDB to debug it. The main problems this project solves are:

1. Getting the GDB stub to compile on the Xinu source tree.

2. Augmenting the `cs-console` command to patch through the GDB protocol 
   to a local instance of GDB.

The final architecture to allow remote debugging then looks like: 

```
+---------+         +------------+
| Galileo | Serial  |    Xinu    |
|  Board  <--------->   Server   |
|         |         |            |
+---------+         +-----^------+
                          |  Network
      +-------------------|-------+
      |  +-----+    +-----v----+  |
      |  | GDB |    |cs-console|  |
      |  |     <---->          |  |
      |  +-----+    +----------+  |
      |      Xinu Workstation     |
      +---------------------------+

```

In order to allow regular output and the GDB protocol to both be sent through
serial, we prefix each GDB message with `<STX>G` where STX is the ASCII start
of text character (`\x02`). Each message is terminated with `<EOT>` (end of
transmission `\x04`).

Our re-written version of `cs-console` does the following:

* Opens up a server socket that gdb can connect to as a target.

* Prints output as the original `cs-console` normally would but upon
  encountering `<STX>G` will stop printing and start piping the messages
  through to gdb.

* Forward any data sent by gdb through to the galileo board.
