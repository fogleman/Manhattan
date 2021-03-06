from imposm.parser import OSMParser
from math import radians
from util import mercator, laea, hex_color, join_ways
import cairo
import random
import shapefile

M = 6
WIDTH = M * 1024
HEIGHT = M * 2048
SCALE = M * 500000
LAT, LNG = (40.777274, -73.967161)

BACKGROUND = hex_color('#1E1E20')

COLORS = [
    hex_color("#730046"),
    hex_color("#BFBB11"),
    hex_color("#FFC200"),
    hex_color("#E88801"),
    hex_color("#C93C00"),
]

def project(lat, lng):
    return laea(lat, lng, LAT, LNG, SCALE)
    # return mercator(lat, lng, SCALE)

def clip_to_manhattan(dc):
    sf = shapefile.Reader('shp/nybb_15b/cleaned.shp')
    for item in sf.shapeRecords():
        if item.record[1] != 'Manhattan':
            continue
        shape = item.shape
        parts = list(shape.parts) + [len(shape.points)]
        for i1, i2 in zip(parts, parts[1:]):
            points = [project(y, x) for x, y in shape.points[i1:i2]]
            for x, y in points:
                dc.line_to(x, y)
            dc.new_sub_path()
    dc.clip()
    # dc.set_source_rgb(1, 1, 1)
    # dc.paint()

def create_dc(surface):
    dc = cairo.Context(surface)
    dc.set_source_rgb(*BACKGROUND)
    dc.paint()
    dc.set_line_cap(cairo.LINE_CAP_ROUND)
    dc.set_line_join(cairo.LINE_JOIN_ROUND)
    tx, ty = project(LAT, LNG)
    dc.translate(WIDTH / 2, HEIGHT / 2)
    dc.rotate(radians(-29))
    dc.translate(-tx, -ty)
    return dc

class Handler(object):
    def __init__(self):
        self.nodes = {}
        self.ways = {}
        self.building_ways = []
        self.building_relations = []
        self.surface = cairo.ImageSurface(cairo.FORMAT_RGB24, WIDTH, HEIGHT)
        self.dc = create_dc(self.surface)
        clip_to_manhattan(self.dc)
    def on_coords(self, coords):
        for osmid, lng, lat in coords:
            self.nodes[osmid] = project(lat, lng)
    def on_nodes(self, nodes):
        for osmid, _, (lng, lat) in nodes:
            self.nodes[osmid] = project(lat, lng)
    def on_ways(self, ways):
        for osmid, tags, refs in ways:
            self.ways[osmid] = refs
            if 'building' in tags:
                self.building_ways.append(osmid)
    def on_relations(self, relations):
        for _, tags, members in relations:
            if 'building' in tags:
                self.building_relations.append(members)
    def join_ways(self, ways):
        result = []
        todo = []
        for osmid in ways:
            refs = self.ways[osmid]
            if refs[0] == refs[-1]:
                result.append(refs)
            else:
                todo.append(refs)
        result.extend(join_ways(todo, []) or todo)
        return result
    def render(self):
        dc = self.dc
        for osmid in self.building_ways:
            dc.set_source_rgb(*random.choice(COLORS))
            self.render_way(osmid)
            dc.fill()
        for members in self.building_relations:
            outer = []
            inner = []
            for osmid, member_type, role in members:
                if member_type == 'way':
                    if role == 'outer':
                        outer.append(osmid)
                    if role == 'inner':
                        inner.append(osmid)
            dc.set_source_rgb(*random.choice(COLORS))
            for refs in self.join_ways(outer):
                self.render_refs(refs)
                dc.fill()
            dc.set_source_rgb(*BACKGROUND)
            for refs in self.join_ways(inner):
                self.render_refs(refs)
                dc.fill()
    def render_refs(self, refs):
        points = [self.nodes[x] for x in refs]
        for x, y in points:
            self.dc.line_to(x, y)
    def render_way(self, osmid):
        refs = self.ways[osmid]
        self.render_refs(refs)

def main():
    h = Handler()
    p = OSMParser(None, h.on_nodes, h.on_ways, h.on_relations, h.on_coords)
    p.parse('osm/nyc.osm.pbf')
    h.render()
    h.surface.write_to_png('output.png')

if __name__ == '__main__':
    main()
