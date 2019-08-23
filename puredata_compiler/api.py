from typing import List, Tuple, Union, Sequence, Dict, Optional, Any, Callable
import collections.abc
import re


def escape(text: str) -> str:
    save = re.sub(r'\\', '\\\\', text)
    save = re.sub(r';', ' \\; ', save)
    save = re.sub(r',', ' \\, ', save)
    save = re.sub(r'\$(?=[0-9])', '\\$', save)
    return save


def unescape(text: str) -> str:
    disp = re.sub(r' (?<!\\)\\; ', '\n', text)
    disp = re.sub(r' (?<!\\)\\, ', ',', disp)
    disp = re.sub(r'(?<!\\)\\$', '$', disp)
    lines = [l.strip() for l in disp.split('\n')]
    return '\n'.join(lines)


def get_display_lines(text: str) -> List[str]:
    display_text = unescape(text)
    lines = []
    for line in display_text.splitlines():
        wrapped = re.findall(r'[ ]*(?:.{1,60}(?:\s|$)|.{60})', line)
        lines.extend(filter(lambda x: len(x) > 0, map(str.strip, wrapped)))
    return lines


class Node(collections.abc.Sequence):
    """Represents one element in a PureData patch"""
    parameters: Dict[str, Any]
    hidden: bool = False

    class Outlet:
        owner: 'Node'
        index: int

        def __init__(self, owner: 'Node', index: int):
            self.owner = owner
            self.index = index

    def __getitem__(self, key) -> 'Node.Outlet':
        return Node.Outlet(self, key)

    def __len__(self):
        return 256

    @property
    def position(self) -> Tuple[int, int]:
        if self.hidden:
            return (-1, -1)
        return (self.parameters['x_pos'], self.parameters['y_pos'])

    @property
    def size(self) -> Tuple[int, int]:
        return (0, 0)

    def get_next_position(self, new_row: float, new_col: float) -> Tuple[int, int]:
        x_pos, y_pos = self.position
        dx, dy = self.size
        if new_row < 1:
            x_pos += dx
            new_col -= 1
        else:
            y_pos += dy + int(25 * (new_row - 1))
        x_pos += max(0, int(50 * new_col))
        return (x_pos, y_pos)


class Obj(Node):
    parameters: Dict[str, Any]

    def __init__(self, x_pos: int, y_pos: int, text: str):
        self.parameters = {'x_pos': x_pos,
                           'y_pos': y_pos,
                           'text': escape(text)}

    def __str__(self):
        return '#X obj {x_pos} {y_pos} {text};\n'.format(**self.parameters)

    @property
    def size(self) -> Tuple[int, int]:
        display_lines = get_display_lines(self.parameters['text'])
        max_chars = max([len(l) for l in display_lines], default=0)
        x_size = max(50, 20 + max_chars * 6)
        y_size = 10 + 15 * len(display_lines)
        return (x_size, y_size)


class Msg(Node):
    def __init__(self, x_pos: int, y_pos: int, text: str):
        self.parameters = {'x_pos': x_pos,
                           'y_pos': y_pos,
                           'text': escape(text)}

    def __str__(self):
        return '#X msg {x_pos} {y_pos} {text};\n'.format(**self.parameters)

    @property
    def size(self) -> Tuple[int, int]:
        display_lines = get_display_lines(self.parameters['text'])
        max_chars = max([len(l) for l in display_lines], default=0)
        x_size = max(50, 20 + max_chars * 6)
        y_size = 10 + 15 * len(display_lines)
        return (x_size, y_size)


class FloatAtom(Node):
    def __init__(self, x_pos: int, y_pos: int, width: int = 5,
                 upper_limit: int = 0, lower_limit: int = 0,
                 label: str = '-', receive: str = '-', send: str = '-'):
        self.parameters = {'x_pos': x_pos,
                           'y_pos': y_pos,
                           'width': width,
                           'upper_limit': upper_limit,
                           'lower_limit': lower_limit,
                           'label': label,
                           'receive': receive,
                           'send': send}

    def __str__(self):
        return ('#X floatatom {x_pos} {y_pos} {width} {upper_limit} '
                '{lower_limit} {label} {receive} {send};\n'
                ).format(**self.parameters)

    @property
    def size(self) -> Tuple[int, int]:
        return (50, 25)


class Subpatch(Node):
    src: 'Patch'

    def __init__(self, x_pos: int, y_pos: int, name: str, src: 'Patch'):
        self.src = src
        self.parameters = {'x_pos': x_pos,
                           'y_pos': y_pos,
                           'name': name}

    def __str__(self):
        return '#N canvas 0 0 300 180 (subpatch) 0;\n' + \
               self.src.subpatch_str() + \
               '#X restore {x_pos} {y_pos} pd {name};\n'.format(
                   **self.parameters)

    @property
    def size(self):
        x_size = max(50, 20 + len('pd ' + self.parameters['name']) * 6)
        return (x_size, 25)


class Array(Node):
    def __init__(self, name: str, length: int, element_type: str = 'float',
                 save_flag: int = 0):
        self.hidden = True
        self.parameters = {'name': name,
                           'length': length,
                           'element_type': element_type,
                           'save_flag': save_flag}

    def __str__(self):
        return '#X array {name} {length} {element_type} {save_flag};\n'.format(
            **self.parameters)


class Connection:
    source: int
    outlet_index: int
    sink: int
    inlet_index: int

    def __init__(self, source: int, outlet_index: int, sink: int,
                 inlet_index: int):
        self.source = source
        self.outlet_index = outlet_index
        self.sink = sink
        self.inlet_index = inlet_index

    def __str__(self):
        return '#X connect {} {} {} {};\n'.format(self.source,
                                                  self.outlet_index,
                                                  self.sink, self.inlet_index)


OutletList = Union[Node.Outlet, Sequence[Node.Outlet]]


class Patch:
    """Represents a PureData patch, stores its nodes and connections"""
    nodes: List[Node]
    connections: List[Connection]
    row_head: Optional[Node]
    row_tail: Optional[Node]
    creators: Dict[str, Callable]

    def __init__(self):
        self.nodes = []
        self.connections = []
        self.row_head = None
        self.row_tail = None
        self.creators = {'obj': self.create_obj,
                         'msg': self.create_msg,
                         'floatatom': self.create_floatatom,
                         'subpatch': self.create_subpatch,
                         'array': self.create_array,
                         'connect': self.add_connections}

    def resolve_position(self,
                         x_pos: int,
                         y_pos: int,
                         new_row: float,
                         new_col: float) -> Tuple[int, int, Callable[[Node], None]]:
        absolute = (x_pos >= 0 and y_pos >= 0)
        if not absolute:
            if new_row < 1:
                anchor = self.row_tail
            else:
                anchor = self.row_head
            if anchor is None:
                x_pos, y_pos = (25, 25)
            else:
                x_pos, y_pos = anchor.get_next_position(new_row, new_col)

        def position_update(node: Node):
            self.row_tail = node
            if absolute or self.row_head is None or new_col > 0 or new_row >= 1:
                self.row_head = node

        return (x_pos, y_pos, position_update)

    def create_obj(
            self,
            text: str,
            *connections: OutletList,
            new_row: float = 1,
            new_col: float = 0,
            x_pos: int = -1,
            y_pos: int = -1) -> Obj:
        """Create an object and add it to the patch

        Parameters
        ----------
        text : str
            the object content

        \\*connections : Node.Outlet or tuple of Node.Outlet
            zero or more outlets to connect to the new object

        new_row : float, optional
            0 to continue current row, 1 to add a new row.
            Values greater than 1 add a top margin.

        new_col : float, optional
            0 to keep current baseline, 1 to set new baseline.
            Values greater than 1 add a left margin.

        x_pos : int, optional
            Absolute x-position for the object. Overrides new_row and new_col
            if set.

        y_pos : int, optional
            Absolute y-position for the object. Overrides new_row and new_col
            if set.

        Returns
        -------
        node : Obj
            The created object
        """
        x_pos, y_pos, pos_update = self.resolve_position(
            x_pos, y_pos, new_row, new_col)
        node = Obj(x_pos, y_pos, text)
        self.nodes.append(node)
        self.add_connections(node, *connections)
        pos_update(node)
        return node

    def create_msg(
            self,
            text: str,
            *connections: OutletList,
            new_row: float = 1,
            new_col: float = 0,
            x_pos: int = -1,
            y_pos: int = -1) -> Msg:
        """Create a message object and add it to the patch

        Parameters
        ----------
        text : str
            the message object content

        \\*connections : Node.Outlet or tuple of Node.Outlet
            zero or more outlets to connect to the new object

        new_row : float, optional
            0 to continue current row, 1 to add a new row.
            Values greater than 1 add a top margin.

        new_col : float, optional
            0 to keep current baseline, 1 to set new baseline.
            Values greater than 1 add a left margin.

        x_pos : int, optional
            Absolute x-position for the object. Overrides new_row and new_col
            if set.

        y_pos : int, optional
            Absolute y-position for the object. Overrides new_row and new_col
            if set.

        Returns
        -------
        node : Msg
            The created message object
        """
        x_pos, y_pos, pos_update = self.resolve_position(
            x_pos, y_pos, new_row, new_col)
        node = Msg(x_pos, y_pos, text)
        self.nodes.append(node)
        self.add_connections(node, *connections)
        pos_update(node)
        return node

    def create_floatatom(self, *connections: OutletList,
                         new_row: float = 1,
                         new_col: float = 0,
                         x_pos: int = -1,
                         y_pos: int = -1) -> FloatAtom:
        """Create a number object and add it to the patch

        Parameters
        ----------
        \\*connections : Node.Outlet or tuple of Node.Outlet
            zero or more outlets to connect to the new object

        new_row : float, optional
            0 to continue current row, 1 to add a new row.
            Values greater than 1 add a top margin.

        new_col : float, optional
            0 to keep current baseline, 1 to set new baseline.
            Values greater than 1 add a left margin.

        x_pos : int, optional
            Absolute x-position for the object. Overrides new_row and new_col
            if set.

        y_pos : int, optional
            Absolute y-position for the object. Overrides new_row and new_col
            if set.

        Returns
        -------
        node : Floatatom
            The created number object
        """
        x_pos, y_pos, pos_update = self.resolve_position(
            x_pos, y_pos, new_row, new_col)
        node = FloatAtom(x_pos, y_pos)
        self.nodes.append(node)
        self.add_connections(node, *connections)
        pos_update(node)
        return node

    def create_subpatch(
            self,
            name: str,
            src: 'Patch',
            *connections: OutletList,
            new_row: float = 1,
            new_col: float = 0,
            x_pos: int = -1,
            y_pos: int = -1) -> Subpatch:
        """Insert a subpatch into the patch

        Parameters
        ----------
        name : str
            the subpatch name

        src : Patch
            the contained patch

        \\*connections : Node.Outlet or tuple of Node.Outlet
            zero or more outlets to connect to the new object

        new_row : float, optional
            0 to continue current row, 1 to add a new row.
            Values greater than 1 add a top margin.

        new_col : float, optional
            0 to keep current baseline, 1 to set new baseline.
            Values greater than 1 add a left margin.

        x_pos : int, optional
            Absolute x-position for the object. Overrides new_row and new_col
            if set.

        y_pos : int, optional
            Absolute y-position for the object. Overrides new_row and new_col
            if set.

        Returns
        -------
        node : Subpatch
            The created subpatch object
        """
        x_pos, y_pos, pos_update = self.resolve_position(
            x_pos, y_pos, new_row, new_col)
        node = Subpatch(x_pos, y_pos, name, src)
        self.nodes.append(node)
        self.add_connections(node, *connections)
        pos_update(node)
        return node

    def create_array(self, name: str, length: int) -> Array:
        """Declare an array in the subpatch.

        Parameters
        ----------
        name : str
            the subpatch name

        length : int
            the array length

        Returns
        -------
        node : Array
            The created array

        Notes
        -----
        The array will not have a graph. Its contents are not stored.
        """
        node = Array(name, length)
        self.nodes.append(node)
        return node

    def add_connections(self, node: Node, *connections: OutletList) -> None:
        """Add connections to a node in this patch

        Parameters
        ----------
        node : Node
            the subpatch name

        \\*connections : Node.Outlet or tuple of Node.Outlet
            zero or more outlets to connect to the node
        """
        inlet_owner_index = self.nodes.index(node)
        for inlet_index, outlets in enumerate(connections):
            if isinstance(outlets, Node.Outlet):
                outlets = (outlets,)
            if len(outlets) == 0:
                continue
            try:
                assert not isinstance(outlets, Node)
                assert isinstance(outlets[0], Node.Outlet)
            except (AssertionError, IndexError):
                raise Exception("Malformed connections list")
            for o in outlets:
                outlet_owner_index = self.nodes.index(o.owner)
                self.connections.append(Connection(outlet_owner_index,
                                                   o.index, inlet_owner_index,
                                                   inlet_index))

    def get_creators(self, names: str) -> Sequence[Callable]:
        """Get a list of functions to compose the patch

        Parameters
        ----------
        names : str
            a comma-separated list of function names
            allowed values: obj, msg, floatatom, subpatch, array, connect

        Returns
        -------
        creators : tuple of functions
        """
        name_list = [s.strip() for s in names.split(',')]
        return tuple(self.creators[k] for k in name_list if (k in self.creators.keys()))

    def __str__(self):
        out = '#N canvas 0 50 1000 600 10;\n'
        out += self.subpatch_str().rstrip()
        return out

    def subpatch_str(self):
        out = ''.join([str(n) for n in self.nodes])
        out += ''.join([str(c) for c in self.connections])
        return out


def write_file(filename: str, data: str):
    fp = open(filename, 'w')
    fp.write(data)
    fp.close()
