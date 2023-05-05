# coding: utf-8

# directory element object
class DirItem():

    def __init__(self, filename, dispname, size_type):
        self._filename = filename
        self._dispname = dispname if dispname else filename
        if size_type == '<dir>':
            self._size = 0
            self._is_dir = True
        else:
            self._size = int(size_type)
            self._is_dir = False

    def __str__(self):
        return '%s, %s, %s' % (
            self._filename, self._dispname, ('<dir>' if self._is_dir else '<file>'))

    @property
    def is_dir(self):
        return self._is_dir

    @property
    def filename(self):
        return self._filename

    @property
    def dispname(self):
        return self._dispname

    def exact_match(self, keyword):
        if keyword in (self._filename, self._dispname):
            return True


# directory list object
class DirList():

    def __init__(self):
        self._items = []

    @property
    def items(self):
        return self._items

    def add_item(self, items):
        if isinstance(items, list):
            self._items.extend(items)
        elif isinstance(items, DirItem):
            self._items.append(items)

    def add(self, filename, dispname, size_type):
        item = DirItem(filename, dispname, size_type)
        self.add_item(item)

    def find_item(self, keyword):
        for i in self._items:
            if i.exact_match(keyword):
                return i

    def find_items(self, namelist):
        dirlist = DirList()
        for keyword in namelist:
            for i in self._items:
                if i.exact_match(keyword):
                    dirlist.add_item(i)
        return dirlist
