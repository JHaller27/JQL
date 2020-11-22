# JQL

Table of Contents
=================
* [Overview](#overview)
* [Language Spec](#language-spec)
  * [Path](#path)
  * [Operators](#operators)
    * [Order of Operations](#order-of-operations)
    * [Not (not)](#not-not)
    * [And (and)](#and-and)
    * [Or (or)](#or-or)
    * [Exists (ex)](#exists-ex)
    * [Not Exists (nex)](#not-exists-nex)
    * [Contains (in)](#contains-in)
    * [Not Contains (nin)](#not-contains-nin)
    * [Equals (eq)](#equals-eq)
    * [Matches (mt/rx)](#matches-mtrx)
    * [Less Than (lt)](#less-than-lt)
    * [Less Than or Equal (le)](#less-than-or-equal-le)
    * [Greater Than (gt)](#greater-than-gt)
    * [Greater Than or Equal (ge)](#greater-than-or-equal-ge)
    * [Len (len)](#len-len)
    * [Is an Object (obj)](#is-an-object-obj)
    * [Is an Array (arr)](#is-an-array-arr)
    * [Is a String (str)](#is-a-string-str)
    * [Is a Number (num)](#is-a-number-num)

# Overview

JSON Query Language (JQL), as one might expect, is a language used to query JSON data.
It's primary purpose is to determine if a given JSON matches certain conditions (as opposed to competing with SQL and performing joins and aggregations, which are not supported by JQL).

# Language Spec

All expressions are of the form `<operator> <path> [params]` (i.e. prefix notation).

Expressions may be conjoined to create complex expressions.

Note: This implementation does not currently support passing two paths as parameters.

## Path

A JQL property-path (or just "path") denotes the list of property keys to search through.

Property names start with a `.` (period).

Arrays are denoted with `[]` (square-brackets).
If the brackets are left empty (i.e. "ambiguously indexed"), all elements are considered (i.e. "if some element matches...").
If given an index (e.g. `[0]`), only the element at that index is considered.

Note that `-in ...SomeList` works the same as `-eq ...SomeList[]` where the elements of `...SomeList[]` are primitive (strings or numbers).
However, `-in` can _also_ search for the existence of a property.
So `-in ...SomeObj SomeKey` and `-ex ...SomeObj.SomeKey` are both valid and equivalent.

In other words, paths with `[]` can be said as "some element of <path>". E.g. `-ex .Titles` can be pronounced as "The Titles property exists"
whereas `-ex .Titles[]` can be pronounced as "**Some element of** the Titles property exists".

**Example**

Consider the following JSON:
```json
{
    "Product": {
        "Options": [
            {
                "Description": "Good Bye World"
            },
            {
                "Description": "Hello World"
            }
        ]
    }
}
```

The property-path for "Hello world" is `.Product.Options[1].Description`

The property-path for all Descriptions is `.Product.Options[].Description`

## Operators

### Order of Operations
Parentheses are not currently supported by JQL, so it is important to note the order of operations.

Operators are evaluated (roughly) in the order below.

To help, usages denoted with `<path>` or `<param>` must always be followed by a path or literal value.
Usages denoted with `<expression>` must always be some other operation.
Usages that may be either a literal or an expression are denoted like `<param|expr>` (i.e. "literal parameter or expression").

Additionally, in general, numbers are compared directly, strings are compared case-insensitive-alphabetically.

**Example**

To check if the property-path ".Product.Price" (a number) is outside the range 0-99 (inclusive)...

`-not -and -gte ".Product.Price" 0 -lt ".Product.Price" 100`

This roughly translates to `!(0 <= Product.Price < 100)`

### Not (not)

Usage: `-not <expression>`

Negates the following `<expression>`.


### And (and)

Usage: `-and <expression1> <expression2>`

Resolves to true when both `expression1` AND `expression2` are true.


### Or (or)

Usage: `-or <expression1> <expression2>`

Resolves to true when either `expression1` OR `expression2` (or both) are true.


### Exists (ex)

Usage: `-ex <path>`

Resolves to true if `path` is defined.


### Not Exists (nex)

Usage: `-nex <path>`

Equivalent to `-not -ex <path>`

Resolves to true if `path` is undefined.


### Contains (in)

Usage: `-in <path|expr> <param|expr>`

Resolves to true if `param|expr` is contained in `path|expr`


### Not Contains (nin)

Usage: `-nin <path|expr> <param|expr>`

Equivalent to `-not -in <param|expr> <path|expr>`

Resolves to true if `param|expr` is not contained in `path|expr`


### Equals (eq)

Usage: `-eq <path|expr> <param|expr>`
where the value of `path|expr` and `param|expr` is a string or number.

Resolves to true if the value of `path|expr` exactly matches `param|expr`.


### Not Equals (ne)

Usage: `-ne <path|expr> <param|expr>`
where the value of `path|expr` and `param|expr` is a string or number.

Equivalent to `-not -eq <path|expr> <param|expr>`

Resolves to true if the value of `path|expr` exactly matches `param|expr`.


### Matches (mt/rx)

Usage:
`-mt <path|expr> <param|expr>`
OR
`-rx <path|expr> <param|expr>`

where the value of `<path|expr>` is a string or number, and `param|expr` is a regular expression.

Resolves to true if the value of `path|expr` matches the regular expression in `param|expr`.

Note: Regular expressions that also appear to be a valid property-path (e.g. `.tilities[123456789]`) will be interpreted as a property-path.


### Less Than (lt)

Usage: `-lt <path|expr> <param|expr>`
where the value of `path|expr` and `param|expr` is a string or number.

Resolves to true if the value of `path|expr` is less than `param|expr`.


### Less Than or Equal (le)

Usage: `-lt <path|expr> <param|expr>`
where the value of `path|expr` and `param|expr` is a string or number.

Resolves to true if the value of `path|expr` is less than or equal to `param|expr`.


### Greater Than (gt)

Usage: `-lt <path|expr> <param|expr>`
where the value of `path|expr` and `param|expr` is a string or number.

Resolves to true if the value of `path|expr` is greater than `param|expr`.


### Greater Than or Equal (ge)

Usage: `-lt <path|expr> <param|expr>`
where the value of `path|expr` and `param|expr` is a string or number.

Resolves to true if the value of `path|expr` is greater than or equal to `param|expr`.


### Len (len)

Usage: `-len <path|expr>`

If `<path|expr>` resolves to an object, `-len` resolves to the number of properties.

If `<path|expr>` resolves to an array, `-len` resolves to the number of elements.

If `<path|expr>` resolves to a string or number, `-len` resolves to the length of the string/number (including whitespace and decimals).


### Is an Object (obj)

Usage: `-obj <path>`

Resolves to true if `path` is an object.

### Is an Array (arr)

Usage: `-arr <path>`

Resolves to true if `path` is an array.


### Is a String (str)

Usage: `-str <path>`

Resolves to true if `path` is a string.


### Is a Number (num)

Usage: `-num <path>`

Resolves to true if `path` is a number.
