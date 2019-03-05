# Porting Instructions for XKDB

This document outlines how to port the gdb stub for xkdb to a new architecture.

1. Base your work off the pre-existing gdb stub for your architecture. These
   can most easily be found in the [/gdb/stubs](https://sourceware.org/git/gitweb.cgi?p=binutils-gdb.git;a=tree;f=gdb/stubs;h=31b2f77e5e3b6d1758add0a876a2b51aa8a45026;hb=HEAD)
   folder from the gdb source tree. Some googling can lead you to stubs for
   more exotic architectures.

2. Complete the following blank functions in the stub:

   * `int getDebugChar()` - Read a byte from serial. Either call into
     XINU's `kgetc` or reimplement it.

   * `void putDebugChar(int)` - Write a byte to serial. Either call into
     XINU's `kputc` or reimplement it.

   * `void exceptionHandler (int exception_number, void *exception_address)` -
     Install an exception handler for a given exception number and the provided
     function. The easiest way to implement this is to simply call XINU's
     `set_evec` function.

   Please look at the [GDB documentation on stubs](https://sourceware.org/gdb/onlinedocs/gdb/Bootstrapping.html#Bootstrapping)
   and existing stubs for further guidance.

3. Compile the stub into your XINU source tree following the instructions in
   the [README](README.md) and test.