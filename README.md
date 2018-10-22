[![Build Status](https://travis-ci.org/ammaraskar/xkdb.svg?branch=master)](https://travis-ci.org/ammaraskar/xkdb)
[![Code Coverage](https://codecov.io/gh/ammaraskar/xkdb/branch/master/graph/badge.svg)](https://codecov.io/gh/ammaraskar/xkdb)
# xkdb
Xinu Kernel DeBugger is a project that allows you to use GDB on remote
xinu backends.

![Demo](https://i.imgur.com/9S6KIva.gif)

## How to Use

1. **Compile stub into your xinu build**

   Move `stub/i386-stub.c` into `system/i386.stub.c`.

   Make the following change in your `system/initialize.c` file, firstly add
   these prototypes on the top of the file with the other externs:

   ```c
   extern void set_debug_traps(); // Add these two function
   extern void breakpoint();      // prototypes
   ```

   Next add these two function calls near the bottom of the `sysinit()` 
   function (changes marked with `//` comments):

   ```c
   static  void    sysinit()
   {
   ...
       /* Create a ready list for processes */

       readylist = newqueue();

       set_debug_traps(); // Add these two
       breakpoint();      // function calls here
        
       /* Initialize the real time clock */
    
       clkinit();
   ...
   }
    ```

2. **Add debug flag to your xinu Makefile**

   Open up `compile/Makefile` and find the line with the compiler flags, it
   should look like this: ```CFLAGS  = -march=i586 ...```

   Add `-g` to the `CFLAGS` variable so it looks along the lines of:
   ```CFLAGS  = -g -march=i586 -m32 -fno-builtin...```

3. **Use xkdb.py to connect to a backend board**

   Change into your Xinu `/compile` directory. You can then run xkdb with
   `~/path/to/xkdb/py-console/xkdb.py`

   This will automatically upload the xinu image file and power cycle the
   backend. Use the `--help` option view all the options available for
   `xkdb.py`

4. **Connect GDB to the backend**

   Open up another terminal and run `gdb -x ~/.xkdb`

   GDB will be unresponsive until the backend is fully booted, then you should
   see the breakpoint be hit.


*Tip*: Add `~/path/to/xkdb/py-console` to your `PATH` variable so you can
simply use the command `xkdb.py` instead of specifying the full path.

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
