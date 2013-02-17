import array
import sys

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

SECTORS = (0, 7, 14, 5, 12, 3, 10, 1, 8, 15, 6, 13, 4, 11, 2, 9)

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

def log(text):

    if DEBUG:
        sys.stderr.write(text + "\n")

def tostr(a):
    st = ''
    i = 0
    for c in a:
        st += "%d %d %c\n" % (i, c, c)
        i += 1
    return st

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

    def read_sector(self, track, sector):

        log("read_sector: track=%d sector=%d" % (track, sector))
        sector = SECTORS[sector]
        return self.dsk.read_sector(track, sector)

    def read_track_data(self, track):

        data = array.array('B')
        for i in xrange(16):
            data += self.read_sector(track, i)
        return data

    def read_block(self, numer, bytes):
        log("read_block: numer=%d bytes=%d" % (numer, bytes))
        t = 4 + numer // 4
        #t = numer / 4
        n = numer % 4
        data = array.array('B')
        for i in xrange(4):
            data += self.read_sector(t, n * 4 + i)
        if bytes > 1024:
            bytes = 1024
        log("read_block: data=%s" % tostr(data))
        return data[:bytes], bytes

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
        #log("list_entry number=%d entry=%s" % (number, entry))
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
            log("read_dir: a=%s" % str(a))
            self.entries.append(a)

    def get_size(self, entry):
        e = filter(lambda x: (x[NAME] == entry[NAME]) and \
        (x[NR_OF_DIR] == entry[NR_OF_DIR]), self.entries)
        size = 0
        for i in e:
            size += get_size(i)
        return size

    def find_entry(self, name, nr):
        log("find_entry: name = %s, nr = %d self.names=%s" % (name, nr, self.names))
        if name in self.names:
            log("name in self.names")
            #log("self.entries = %s" % self.entries)
            i = self.names[name]
            log("i = %d" % i)
            log("len=%d" % len(self.entries))
            entry = self.entries[i]
            log("entry = %s" % str(entry))
            if nr == 0:
                return entry
            else:
                name = name.split("/")[-1]
                for i in self.entries:
                    if i[NAME] == name and i[NO] == nr and i[NR_OF_DIR] == entry[NR_OF_DIR]:
                        return i
        else:
            log("name in self.names failed")

    def read_file(self, name):
        log("read_file: name=%s" % name)
        d = array.array('B')
        nr = 0
        log("nr=%d" % nr)
        while True:
            entry = self.find_entry(name, nr)
            if not entry:
                log("not entry")
                return d
            log("read_file: entry=%s" % str(entry))
            left = get_size(entry)
            log("left=%d" % left)
            for i in entry[-1]:
                log("i = %d, left = %d" % (i, left))
                if i == 0:
                    return d
                data, r = self.read_block(i, left)
                log("ddd=%s" % tostr(data))
                left -= r
                d.extend(data)
            if entry[N128] == 128:
                nr += 1
            else:
                break
        return d

    def get_data(self, name, length, offset):
        log("get_data: name = %s length = %d offset = %d" % (name, length, offset))
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
        self.Tra = []
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

        log("DSK: number_of_tracks = %d number_of_sides = %d block_size = %d" \
        % (self.number_of_tracks, self.number_of_sides, self.block_size))
        log("DSK: extended = %d" % self.extended)
        log("tracksizes = %s" % self.track_sizes)

    def read_sector(self, track, sector):

        log("DSK: read_sector sector = %d" % sector)
        begin = 256 + 256 * 17 * track + 256 + sector * 256
        end = begin + 256
        log("begin = %d end=%d" % (begin, end))
        return self.data[begin:end]

    def show_info(self, prefix, a):
        info = ''.join(map(chr, a))
        log("prefix=%s info=%s" % (prefix, info))


    def show_track_info(self, number):
        t = self.data[self.tracks[number]:self.tracks[number]+0x18+128]
        self.show_info('Track info:', t[:0xc])
        log("Track number = %d" % t[0x10])
        log("Side number = %d" % t[0x11])
        log("Sector_size = %d" % t[0x14])
        log("Number of sectors = %d" % t[0x15])
        log("GAP#3 length = %d" % t[0x16])
        log("Filler byte = %d" % t[0x17])
        log("Sector info = %s" % t[0x18:0x18+128])

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
