import array

NAME = 1
NR_OF_DIR = 2
NO = 3
LAST = 4
N128 = 5

SECTOR_SIZE = 0
NUMBER_OF_SECTORS = 1
FILLER_BYTE = 2
DATA_BEGIN = 3
DATA_END = 4

DEBUG = 0

def dirFromList(list):
    """
    Return a properly formatted list of items suitable to a directory listing.
    [['a', 'b', 'c']] => [[('a', 0), ('b', 0), ('c', 0)]]
    """
    return [[(x, 0) for x in list]]

def getDepth(path):
    """
    Return the depth of a given path, zero-based from root ('/')
    """
    if path == '/':
        return 0
    else:
        return path.count('/')

def getParts(path):
    """
    Return the slash-separated parts of a given path as a list
    """
    if path == '/':
        return [['/']]
    else:
        return path.split('/')

def name(tekst):
    t = filter(lambda c: c != 32, tekst)
    return "".join(map(lambda x: chr(x & 127), t))


def get_size(entry):
    if entry[LAST] == 0:
        return entry[N128] * 128
    return entry[N128] * 128 - 256 + entry[LAST]

class TOS:
    """
    """
    def __init__(self, dsk):
        self.dsk = dsk
        self.dirs = {}
        self.names = {}
        self.read_disk()
        self.read_dir()
        self.gen_names()

    def read_track_data(self, track):
        t = self.dsk.get_track_info(track, 0)
        if DEBUG: print "read_track_data:", track, t
        return self.dsk.data[t[DATA_BEGIN]:t[DATA_END]]

    def read_disk(self):
        self.system = self.read_track_data(0) + \
        self.read_track_data(1) + \
        self.read_track_data(2) + \
        self.read_track_data(3)
        self.directory = self.read_track_data(4)

    def list_entry(self, entry, number):
        """
        Returns number, name, dir, no, size_of_last, n128, allocation
        """
        if DEBUG: print "list_entry",number, entry
        nazwa = name(entry[1:0x09])
        n2 = name(entry[0x09:0x0c])
        if n2:
            nazwa += "." + n2
        if entry[0xa] & 128:
            nazwa = "." + nazwa
        nr_of_dir = entry[0]
        no = entry[0x0c]
        size_of_last = entry[0x0d]
        n128 =  entry[0x0f]
        if (n128 == 0) and (size_of_last == 0) and (no == 0) and (nr_of_dir != 255):
            self.dirs[entry[0x10]] = number
        
        #print "Numer podkatalogu:", entry[0]
        #print "Nazwa:", name(entry[1:0x9]) + "." + name(entry[0x9:0xc])
        #if entry[0xa] & 128:
        #    print "hidden"
        #if entry[0xb] & 128:
        #    print "read only"
        #print "Numer kolejnego rekordu", entry[0xc]
        #print "Liczba bajtow w ostatnim sektorze", entry[0xd]
        #print "Liczba 128 *", entry[0xe], entry[0xf]
        #print "Alokacja", entry[0x10:]

        return (number, nazwa, nr_of_dir, no, size_of_last, n128, entry[0xe], entry[0x10:])

    def read_dir(self):
        self.entries = []
        for i in range(128):
            a = self.list_entry(self.directory[i * 32 : i * 32 + 32], i)
            if DEBUG: print a
            self.entries.append(a)

    def read_block(self, numer, bytes):
        if DEBUG: print "read_block: numer=%d bytes=%d" % (numer, bytes)
        t = 4 + numer / 4
        n = numer % 4
        data = self.read_track_data(t)
        if bytes > self.dsk.block_size:
            bytes = self.dsk.block_size
        if DEBUG: print "t=%d n=%d bytes=%d" % (t, n, bytes)
        return (data[n * self.dsk.block_size: n * self.dsk.block_size + bytes],
        bytes)

    def get_size(self, entry):
        e = filter(lambda x: (x[NAME] == entry[NAME]) and \
        (x[NR_OF_DIR] == entry[NR_OF_DIR]), self.entries)
        size = 0
        for i in e:
            size += get_size(i)
        return size

    def find_entry(self, name, nr):

        if name in self.names:
            entry = self.entries[self.names[name]]
            if nr == 0:
                return entry
            else:
                name = name.split("/")[-1]
                for i in self.entries:
                    if i[NAME] == name and i[NO] == nr and i[NR_OF_DIR] == entry[NR_OF_DIR]:
                        return i

    def read_file(self, name):
        d = array.array('B')
        nr = 0
        while True:
            entry = self.find_entry(name, nr)
            if not entry:
                return d
            if DEBUG: print "read_file:", entry
            left = get_size(entry)
            if DEBUG: print "left", left
            for i in entry[-1]:
                if i == 0:
                    return d
                data, r = self.read_block(i, left)
                #print data, r
                left -= r
                d.extend(data)
            if entry[N128] == 128:
                nr += 1
            else:
                break
        return d

    def get_data(self, name, length, offset):
        if DEBUG: print "get_data: name = ", name, "length =",length,"offset =",offset
        data = self.read_file(name)
        #print "data = ", data[offset:offset+length]
        return data[offset:offset+length].tostring()

    def find_dir_entry(self, nr):

        for i in self.entries:
            if (i[N128] == 0) and (i[LAST] == 0) and (i[NO] == 0) and \
            (i[-1][0] == nr):
                return i

    def get_name(self, entry):

        parent = entry[NR_OF_DIR] & 127
        if parent:
            return self.get_name(self.entries[self.dirs[parent]]) + '/' + entry[NAME]
        return entry[NAME]

    def gen_names(self):

        for i in xrange(1, 128):
            if self.entries[i][NR_OF_DIR] > 128:
                continue
            if self.entries[i][NO] != 0:
                continue
            name = self.get_name(self.entries[i])
            self.names[name] = i

class DSK:
    """
    """
    def __init__(self, path):
        self.readdisk(path)

    def readdisk(self, path):
        self.f = open(path, "rb").read()
        self.data = array.array('B', self.f)
        self.number_of_tracks = self.data[0x30]
        self.number_of_sides = self.data[0x31]
        #print self.f[:9]
        if self.f[:9] == "EXTENDED ":
            self.extended = True
        else:
            self.extended = False

        if (self.number_of_sides > 1) and (self.number_of_tracks >= 80):
            self.block_size = 4096
        else:
            self.block_size = 1024

        self.size_of_track = self.data[0x32] + 256 * self.data[0x33]
        if self.extended:
            self.track_sizes = self.data[0x34:0x34+self.number_of_tracks * self.number_of_sides]
        else:
            self.track_sizes = [self.size_of_track / 256] * self.number_of_tracks * self.number_of_sides
        self.tracks = []
        n = 0x100
        counter = 0
        for i in xrange(self.number_of_tracks):
            for j in xrange(self.number_of_sides):
                self.tracks.append(n)
                n += self.track_sizes[counter] * 256
                counter += 1
        self.tracks.append(n)

        if DEBUG: print "DSK: number_of_tracks = %d number_of_sides = %d block_size = %d" \
        % (self.number_of_tracks, self.number_of_sides, self.block_size)
        if DEBUG: print "DSK:", self.extended
        if DEBUG: print self.track_sizes

    def show_info(self, prefix, a):
        info = ''.join(map(chr, a))
        if DEBUG: print prefix, info


    def show_track_info(self, number):
        t = self.data[self.tracks[number]:self.tracks[number]+0x18+128]
        self.show_info('Track info:', t[:0xc])
        if DEBUG:
            print "Track number", t[0x10]
            print "Side number", t[0x11]
            print "Sector_size", t[0x14]
            print "Number of sectors",t[0x15]
            print "GAP#3 length", t[0x16]
            print "Filler byte",t[0x17]
            print "Sector info", t[0x18:0x18+128]

    def get_track_info(self, number, side):
        """
        Returns sector_size, number_of_sectors, filler_byte, start_of_data, end_of_data
        """
        tn = number * self.number_of_sides + side
        begin = self.tracks[tn]
        return (self.data[begin + 0x14],
        self.data[begin + 0x15],
        self.data[begin + 0x17],
        begin + 0x100,
        self.tracks[tn+1])

    def show_header(self):
        self.show_info("", self.data[:0x22])
        self.show_info("Creator", self.data[0x22:0x30])
        #print "Number of tracks", self.number_of_tracks
        #print "Size of track", self.size_of_track
        #print "Rozmiar =", 0x100 + self.number_of_tracks * self.number_of_sides * self.size_of_track
        for i in xrange(self.number_of_tracks):
            self.show_track_info(i)
