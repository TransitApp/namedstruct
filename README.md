# namedstruct

This project is a more advanced version of the Python
`struct` module. It has a similar goal of writing
binary data into files, to be read by C/C++. But on
top of creating the binary data, it also allows creating
C++ headers that allow reading the data in. This allows
creating compact binary files. The serialization is similar
to flatBuffers -- the files can be read into memory verbatim on the
C++ side, and data can be read in a structured fashion
without any deserialization effort. That is, the data
is stored in C structures (and similar structures), the
only thing that's needed is pointers to the data.

The namedstruct creates types for each kind of structured data, which
have to be explicitly named. The created C++ classes make accessing
the data convenient. When creating the header files, there
is also some checking whether all types with the same name are
consistent.

The header files can be constructed directly from the created
data objects -- that is there's no need to write a separate
schema to define the structure of the data. That is convenient,
but also dangerous -- the code that creates the objects is the
implicit schema. In order for the C++ files and the incoming
data to be compatibly, the order and types of the data that
is added to the structured objects have to be the same. Also,
if a member is optional, then it _has_ to be present when
creating the header files, otherwise they won't know about
that optional value.

There are several kinds of structured data possible. Atomic values are
integers (1,2,4,8 bytes), chars, strings ('\0'-terminated) and
bitArrays. Structured data can be constructed of these -- either as
structs or as arrays. Additionally, it is possible to create bit-field
values, out of a single integer values. These bitfields are fixed
in terms of how many bits each field uses. Another structure is a
`BitFieldArray`, which is an array of bit-fields structures. These use a non-fixed
number of bits per field -- i.e. every field uses just enough bits to store
the largest value.

References are supported, but they can only refer to child elements.
The overall structure is that of a tree, cycles and or a child having
multiple parents is not supported. Parent pointers are not supported either.
References may be 1,2,4 bytes long. So if it is known that a child
will always be at most be 255 bytes from it's parent, then it is possible
to specify that the reference should use a single byte only.






