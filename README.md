# xkdb
Xinu Kernel DeBugger

## Project Structure

* `stub/` - The gdb stub and changes on the Xinu side to act as
  a remote debugging target.

* `py-console/` - A Python version of the `cs-console` command,
  used to establish a connection to the Xinu backends and pipe
  data in and out through to GDB.