Title: Groups — h5py 3.14.0 documentation        

*   Groups
*   View page source

Groups
=======

Groups are the container mechanism by which HDF5 files are organized. From a Python perspective, they operate somewhat like dictionaries. In this case the “keys” are the names of group members, and the “values” are the members themselves (`Group` and `Dataset`) objects.

Group objects also contain most of the machinery which makes HDF5 useful. The File object does double duty as the HDF5 _root group_, and serves as your entry point into the file:

\>>> f \= h5py.File('foo.hdf5','w')
\>>> f.name
'/'
\>>> list(f.keys())
\[\]

Names of all objects in the file are all text strings (`str`). These will be encoded with the HDF5-approved UTF-8 encoding before being passed to the HDF5 C library. Objects may also be retrieved using byte strings, which will be passed on to HDF5 as-is.

Creating groups
----------------

New groups are easy to create:

\>>> grp \= f.create\_group("bar")
\>>> grp.name
'/bar'
\>>> subgrp \= grp.create\_group("baz")
\>>> subgrp.name
'/bar/baz'

Multiple intermediate groups can also be created implicitly:

\>>> grp2 \= f.create\_group("/some/long/path")
\>>> grp2.name
'/some/long/path'
\>>> grp3 \= f\['/some/long'\]
\>>> grp3.name
'/some/long'

Dict interface and links
-------------------------

Groups implement a subset of the Python dictionary convention. They have methods like `keys()`, `values()` and support iteration. Most importantly, they support the indexing syntax, and standard exceptions:

\>>> myds \= subgrp\["MyDS"\]
\>>> missing \= subgrp\["missing"\]
KeyError: "Name doesn't exist (Symbol table: Object not found)"

Objects can be deleted from the file using the standard syntax:

\>>> del subgroup\["MyDataset"\]

Note

When using h5py from Python 3, the keys(), values() and items() methods will return view-like objects instead of lists. These objects support membership testing and iteration, but can’t be sliced like lists.

By default, objects inside group are iterated in alphanumeric order. However, if group is created with `track_order=True`, the insertion order for the group is remembered (tracked) in HDF5 file, and group contents are iterated in that order. The latter is consistent with Python 3.7+ dictionaries.

The default `track_order` for all new groups can be specified globally with `h5.get_config().track_order`.

### Hard links

What happens when assigning an object to a name in the group? It depends on the type of object being assigned. For NumPy arrays or other data, the default is to create an HDF5 datasets:

\>>> grp\["name"\] \= 42
\>>> out \= grp\["name"\]
\>>> out
<HDF5 dataset "name": shape (), type "<i8">

When the object being stored is an existing Group or Dataset, a new link is made to the object:

\>>> grp\["other name"\] \= out
\>>> grp\["other name"\]
<HDF5 dataset "other name": shape (), type "<i8">

Note that this is not a copy of the dataset! Like hard links in a UNIX file system, objects in an HDF5 file can be stored in multiple groups:

\>>> grp\["other name"\] \== grp\["name"\]
True

### Soft links

Also like a UNIX filesystem, HDF5 groups can contain “soft” or symbolic links, which contain a text path instead of a pointer to the object itself. You can easily create these in h5py by using `h5py.SoftLink`:

\>>> myfile \= h5py.File('foo.hdf5','w')
\>>> group \= myfile.create\_group("somegroup")
\>>> myfile\["alias"\] \= h5py.SoftLink('/somegroup')

If the target is removed, they will “dangle”:

\>>> del myfile\['somegroup'\]
\>>> print(myfile\['alias'\])
KeyError: 'Component not found (Symbol table: Object not found)'

### External links

External links are “soft links plus”, which allow you to specify the name of the file as well as the path to the desired object. You can refer to objects in any file you wish. Use similar syntax as for soft links:

\>>> myfile \= h5py.File('foo.hdf5','w')
\>>> myfile\['ext link'\] \= h5py.ExternalLink("otherfile.hdf5", "/path/to/resource")

When the link is accessed, the file “otherfile.hdf5” is opened, and object at “/path/to/resource” is returned.

Since the object retrieved is in a different file, its “.file” and “.parent” properties will refer to objects in that file, _not_ the file in which the link resides.

Note

Currently, you can’t access an external link if the file it points to is already open. This is related to how HDF5 manages file permissions internally.

Note

The filename is stored in the file as bytes, normally UTF-8 encoded. In most cases, this should work reliably, but problems are possible if a file created on one platform is accessed on another. Older versions of HDF5 may have problems on Windows in particular. See Filenames on different systems for more details.

Reference
----------

_class_ h5py.Group(_identifier_)

Generally Group objects are created by opening objects in the file, or by the method `Group.create_group()`. Call the constructor with a `GroupID` instance to create a new Group bound to an existing low-level identifier.

\_\_iter\_\_()

Iterate over the names of objects directly attached to the group. Use `Group.visit()` or `Group.visititems()` for recursive access to group members.

\_\_contains\_\_(_name_)

Dict-like membership testing. name may be a relative or absolute path.

\_\_getitem\_\_(_name_)

Retrieve an object. name may be a relative or absolute path, or an object or region reference. See Dict interface and links.

\_\_setitem\_\_(_name_, _value_)

Create a new link, or automatically create a dataset. See Dict interface and links.

\_\_bool\_\_()

Check that the group is accessible. A group could be inaccessible for several reasons. For instance, the group, or the file it belongs to, may have been closed elsewhere.

\>>> f \= h5py.open(filename)
\>>> group \= f\["MyGroup"\]
\>>> f.close()
\>>> if group:
...     print("group is accessible")
... else:
...     print("group is inaccessible")
group is inaccessible

keys()

> Get the names of directly attached group members. Use `Group.visit()` or `Group.visititems()` for recursive access to group members.

Returns:

set-like object.

values()

Get the objects contained in the group (Group and Dataset instances). Broken soft or external links show up as None.

Returns:

a collection or bag-like object.

items()

Get `(name, value)` pairs for object directly attached to this group. Values for broken soft or external links show up as None.

Returns:

a set-like object.

get(_name_, _default\=None_, _getclass\=False_, _getlink\=False_)

Retrieve an item, or information about an item. name and default work like the standard Python `dict.get`.

Parameters:

*   **name** – Name of the object to retrieve. May be a relative or absolute path.

*   **default** – If the object isn’t found, return this instead.

*   **getclass** – If True, return the class of object instead; `Group` or `Dataset`.

*   **getlink** – If true, return the type of link via a `HardLink`, `SoftLink` or `ExternalLink` instance. If `getclass` is also True, returns the corresponding Link class without instantiating it.

visit(_callable_)

Recursively visit all objects in this group and subgroups. You supply a callable with the signature:

callable(name) \-> None or return value

name will be the name of the object relative to the current group. Return None to continue visiting until all objects are exhausted. Returning anything else will immediately stop visiting and return that value from `visit`:

\>>> def find\_foo(name):
... """ Find first object with 'foo' anywhere in the name """
...     if 'foo' in name:
...         return name
\>>> group.visit(find\_foo)
'some/subgroup/foo'

The traversal order is lexicographic, account taken of the division in groups and subgroups:

\>>> l \= \[\]
\>>> group.visit(l.append)
\>>> assert l \== sorted(l, key\=lambda x: x.split('/'))

The assertion in the above code fragment should never fail, since list `l` is already sorted.

The traversal order is independent of the `track_order` parameter specified when the objects were created (see `create_group()` and `create_dataset()`). All `visit` methods share this same fixed traversal order.

visititems(_callable_)

Recursively visit all objects in this group and subgroups. Like `Group.visit()`, except your callable should have the signature:

callable(name, object) \-> None or return value

In this case object will be a `Group` or `Dataset` instance.

visit\_links(_callable_)

visititems\_links(_callable_)

These methods are like `visit()` and `visititems()`, but work on the links in groups, rather than the objects those links point to. So if you have two links pointing to the same object, these will ‘see’ both. They also see soft & external links, which `visit()` and `visititems()` ignore.

The second argument to the callback for `visititems_links` is an instance of one of the link classes.

New in version 3.11.

move(_source_, _dest_)

Move an object or link in the file. If source is a hard link, this effectively renames the object. If a soft or external link, the link itself is moved.

Parameters:

*   **source** (_String_) – Name of object or link to move.

*   **dest** (_String_) – New location for object or link.

copy(_source_, _dest_, _name\=None_, _shallow\=False_, _expand\_soft\=False_, _expand\_external\=False_, _expand\_refs\=False_, _without\_attrs\=False_)

Copy an object or group. The source can be a path, Group, Dataset, or Datatype object. The destination can be either a path or a Group object. The source and destination need not be in the same file.

If the source is a Group object, by default all objects within that group will be copied recursively.

When the destination is a Group object, by default the target will be created in that group with its current name (basename of obj.name). You can override that by setting “name” to a string.

Parameters:

*   **source** – What to copy. May be a path in the file or a Group/Dataset object.

*   **dest** – Where to copy it. May be a path or Group object.

*   **name** – If the destination is a Group object, use this for the name of the copied object (default is basename).

*   **shallow** – Only copy immediate members of a group.

*   **expand\_soft** – Expand soft links into new objects.

*   **expand\_external** – Expand external links into new objects.

*   **expand\_refs** – Copy objects which are pointed to by references.

*   **without\_attrs** – Copy object(s) without copying HDF5 attributes.

create\_group(_name_, _track\_order\=None_)

Create and return a new group in the file.

Parameters:

*   **name** (_String_ _or_ _None_) – Name of group to create. May be an absolute or relative path. Provide None to create an anonymous group, to be linked into the file later.

*   **track\_order** – Track dataset/group/attribute creation order under this group if `True`. Default is `h5.get_config().track_order`.

Returns:

The new `Group` object.

require\_group(_name_)

Open a group in the file, creating it if it doesn’t exist. TypeError is raised if a conflicting object already exists. Parameters as in `Group.create_group()`.

create\_dataset(_name_, _shape\=None_, _dtype\=None_, _data\=None_, _\*\*kwds_)

Create a new dataset. Options are explained in Creating datasets.

Parameters:

*   **name** – Name of dataset to create. May be an absolute or relative path. Provide None to create an anonymous dataset, to be linked into the file later.

*   **shape** – Shape of new dataset (Tuple).

*   **dtype** – Data type for new dataset

*   **data** – Initialize dataset to this (NumPy array).

*   **chunks** – Chunk shape, or True to enable auto-chunking.

*   **maxshape** – Dataset will be resizable up to this shape (Tuple). Automatically enables chunking. Use None for the axes you want to be unlimited.

*   **compression** – Compression strategy. See Filter pipeline.

*   **compression\_opts** – Parameters for compression filter.

*   **scaleoffset** – See Scale-Offset filter.

*   **shuffle** – Enable shuffle filter (T/**F**). See Shuffle filter.

*   **fletcher32** – Enable Fletcher32 checksum (T/**F**). See Fletcher32 filter.

*   **fillvalue** – This value will be used when reading uninitialized parts of the dataset.

*   **fill\_time** – Control when to write the fill value. One of the following choices: alloc, write fill value before writing application data values or when the dataset is created; never, never write fill value; ifset, write fill value if it is defined. Default to ifset, which is the default of HDF5 library. If the whole dataset is going to be written by the application, setting this to never can avoid unnecessary writing of fill value and potentially improve performance.

*   **track\_times** – Enable dataset creation timestamps (**T**/F).

*   **track\_order** – Track attribute creation order if `True`. Default is `h5.get_config().track_order`.

*   **external** – Store the dataset in one or more external, non-HDF5 files. This should be an iterable (such as a list) of tuples of `(name, offset, size)` to store data from `offset` to `offset + size` in the named file. Each name must be a str, bytes, or os.PathLike; each offset and size, an integer. The last file in the sequence may have size `h5py.h5f.UNLIMITED` to let it grow as needed. If only a name is given instead of an iterable of tuples, it is equivalent to `[(name, 0, h5py.h5f.UNLIMITED)]`.

*   **allow\_unknown\_filter** – Do not check that the requested filter is available for use (T/F). This should only be set if you will write any data with `write_direct_chunk`, compressing the data before passing it to h5py.

*   **rdcc\_nbytes** – Total size of the dataset’s chunk cache in bytes. The default size is 1024\*\*2 (1 MiB).

*   **rdcc\_w0** – The chunk preemption policy for this dataset. This must be between 0 and 1 inclusive and indicates the weighting according to which chunks which have been fully read or written are penalized when determining which chunks to flush from cache. A value of 0 means fully read or written chunks are treated no differently than other chunks (the preemption is strictly LRU) while a value of 1 means fully read or written chunks are always preempted before other chunks. If your application only reads or writes data once, this can be safely set to 1. Otherwise, this should be set lower depending on how often you re-read or re-write the same data. The default value is 0.75.

*   **rdcc\_nslots** – The number of chunk slots in the dataset’s chunk cache. Increasing this value reduces the number of cache collisions, but slightly increases the memory used. Due to the hashing strategy, this value should ideally be a prime number. As a rule of thumb, this value should be at least 10 times the number of chunks that can fit in rdcc\_nbytes bytes. For maximum performance, this value should be set approximately 100 times that number of chunks. The default value is 521.

require\_dataset(_name_, _shape_, _dtype_, _exact\=False_, _\*\*kwds_)

Open a dataset, creating it if it doesn’t exist.

If keyword “exact” is False (default), an existing dataset must have the same shape and a conversion-compatible dtype to be returned. If True, the shape and dtype must match exactly.

If keyword “maxshape” is given, the maxshape and dtype must match instead.

If any of the keywords “rdcc\_nslots”, “rdcc\_nbytes”, or “rdcc\_w0” are given, they will be used to configure the dataset’s chunk cache.

Other dataset keywords (see create\_dataset) may be provided, but are only used if a new dataset is to be created.

Raises TypeError if an incompatible object already exists, or if the shape, maxshape or dtype don’t match according to the above rules.

Parameters:

**exact** – Require shape and type to match exactly (T/**F**)

create\_dataset\_like(_name_, _other_, _\*\*kwds_)

Create a dataset similar to other, much like numpy’s \_like functions.

Parameters:

*   **name** – Name of the dataset (absolute or relative). Provide None to make an anonymous dataset.

*   **other** – The dataset whom the new dataset should mimic. All properties, such as shape, dtype, chunking, … will be taken from it, but no data or attributes are being copied.

Any dataset keywords (see create\_dataset) may be provided, including shape and dtype, in which case the provided values take precedence over those from other.

create\_virtual\_dataset(_name_, _layout_, _fillvalue\=None_)

Create a new virtual dataset in this group. See Virtual Datasets (VDS) for more details.

Parameters:

*   **name** (_str_) – Name of the dataset (absolute or relative).

*   **layout** (_VirtualLayout_) – Defines what source data fills which parts of the virtual dataset.

*   **fillvalue** – The value to use where there is no data.

build\_virtual\_dataset()

Assemble a virtual dataset in this group.

This is used as a context manager:

with f.build\_virtual\_dataset('virt', (10, 1000), np.uint32) as layout:
layout\[0\] \= h5py.VirtualSource('foo.h5', 'data', (1000,))

Inside the context, you populate a `VirtualLayout` object. The file is only modified when you leave the context, and if there’s no error.

Parameters:

*   **name** (_str_) – Name of the dataset (absolute or relative)

*   **shape** (_tuple_) – Shape of the dataset

*   **dtype** – A numpy dtype for data read from the virtual dataset

*   **maxshape** (_tuple_) – Maximum dimensions if the dataset can grow (optional). Use None for unlimited dimensions.

*   **fillvalue** – The value used where no data is available.

attrs

Attributes for this group.

id

The groups’s low-level identifier; an instance of `GroupID`.

ref

An HDF5 object reference pointing to this group. See Using object references.

regionref

A proxy object allowing you to interrogate region references. See Using region references.

name

String giving the full path to this group.

file

`File` instance in which this group resides.

parent

`Group` instance containing this group.

Link classes
-------------

_class_ h5py.HardLink

Exists only to support `Group.get()`. Has no state and provides no properties or methods.

_class_ h5py.SoftLink(_path_)

Exists to allow creation of soft links in the file. See Soft links. These only serve as containers for a path; they are not related in any way to a particular file.

Parameters:

**path** (_String_) – Value of the soft link.

path

Value of the soft link

_class_ h5py.ExternalLink(_filename_, _path_)

Like `SoftLink`, only they specify a filename in addition to a path. See External links.

Parameters:

*   **filename** (_String_) – Name of the file to which the link points

*   **path** (_String_) – Path to the object in the external file.

filename

Name of the external file as a Unicode string

path

Path to the object in the external file
