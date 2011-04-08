#!/usr/bin/env python

import datetime

from csvkit import typeinference
from csvkit.unicode import UnicodeCSVReader, UnicodeCSVWriter

class InvalidType(object):
    """
    Dummy object type for Column initialization, since None is being used as a valid value.
    """
    pass

class Column(list):
    """
    A normalized data column and inferred annotations (nullable, etc.).
    """
    def __init__(self, index, name, l, normal_type=InvalidType):
        """
        Construct a column from a sequence of values.
        
        If normal_type is not None, inference will be skipped and values assumed to have already been normalized.
        """
        if normal_type != InvalidType:
            t = normal_type
            data = l
        else:
            t, data = typeinference.normalize_column_type(l)
        
        list.__init__(self, data)
        self.index = index
        self.name = name 
        self.type = t
        # self.nullable = ?
        # self.max_length = ?

    def __str__(self):
        return str(self.__unicode__())

    def __unicode__(self):
        """
        Stringify a description of this column.
        """
        return '%3i: %s (%s)' % (self.index, self.name, self.type)

class Table(list):
    """
    A normalized data table and inferred annotations (nullable, etc.).
    """
    def __init__(self, columns=[]):
        """
        Generic constructor. You should normally use a from_* method to create a Table.
        """
        list.__init__(self, columns)

    def __str__(self):
        return str(self.__unicode__())

    def __unicode__(self):
        """
        Stringify a description of all columns in this table.
        """
        return '\n'.join([unicode(c) for c in self])

    def _reindex_columns(self):
        for i, c in enumerate(self):
            c.index = i

    def append(self, column):
        list.append(self, column)
        column.index = len(self) - 1

    def insert(self, i, column):
        list.insert(self, i, column)
        self._reindex_columns()

    def extend(self, columns):
        list.extend(self, columns)
        self._reindex_columns()

    def remove(self, column):
        list.remove(self, column)
        self._reindex_columns()

    def sort(self):
        raise NotImplementedError()

    def reverse(self):
        raise NotImplementedError()

    @classmethod
    def from_csv(self, f, **kwargs):
        """
        Creates a new Table from a file-like object containng CSV data.
        """
        reader = UnicodeCSVReader(f, **kwargs)

        headers = reader.next()

        # Data is processed first into columns (rather than rows) for easier type inference
        data_columns = [[] for c in headers] 

        for row in reader:
            for i, d in enumerate(row):
                try:
                    data_columns[i].append(d.strip())
                except KeyError:
                    # Non-rectangular data is truncated
                    break

        columns = []

        # Convert to "heavy" columns
        for i, c in enumerate(data_columns): 
            columns.append(Column(i, headers[i], c))

        return Table(columns)

    def to_csv(self, output, **kwargs):
        """
        Serializes the table to CSV and writes it to any file-like object.
        """
        out_columns = []
        
        for c in self:
            # Stringify datetimes, dates, and times
            if c.type in [datetime.datetime, datetime.date, datetime.time]:
                out_columns.append([v.isoformat() if v != None else None for v in c])
            else:
                out_columns.append(c)
        
        # Convert columns to rows
        rows = zip(*out_columns)

        # Insert header row
        rows.insert(0, [c.name for c in self])

        writer_kwargs = { 'lineterminator': '\n' }
        writer_kwargs.update(kwargs)

        writer = UnicodeCSVWriter(output, **writer_kwargs)
        writer.writerows(rows)
