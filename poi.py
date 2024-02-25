import json
import struct
from enum import Enum
from pathlib import Path
from io import BytesIO

class Record:
    class Type(Enum):
        deleted = 0
        skipper = 1
        regular = 2
        extended = 3


def to_ov2(lon, lat, label, status=Record.Type.regular.value):
    size = 14 + len(label)
    lon = int(lon * 100000)
    lat = int(lat * 100000)
    label = label.encode('raw_unicode_escape')
    buff = struct.pack(f'<B3i{len(label) + 1}s', status, size, lon, lat, label)
    return buff, size


def skipper_record(ne_long, ne_lat, sw_long, sw_lat, skip=0):
    size = 21 + skip
    ne_long_2 = int(ne_long * 100000)
    ne_lat_2 = int(ne_lat * 100000)
    sw_long_2 = int(sw_long * 100000)
    sw_lat_2 = int(sw_lat * 100000)
    buff = struct.pack(f'<Bi4i', Record.Type.skipper.value, size, ne_long_2, ne_lat_2, sw_long_2, sw_lat_2)
    return buff


station_path = Path(__file__).parent.absolute().joinpath('./out/brands/stations_ARAL Tankstelle_min.json')


def bounding_box(points):
    x_coordinates, y_coordinates = zip(*points)

    return max(x_coordinates), max(y_coordinates), min(x_coordinates), min(y_coordinates)


if __name__ == "__main__":
    json_data = open(station_path, "r").read()
    map_points = []
    cache = BytesIO()
    for entry in json.loads(json_data)[:20]:
        map_points.append((entry["lat"], entry["lng"]))
        new_entry, tmp_size = to_ov2(entry["lng"], entry["lat"],
                       f'[DE-{entry["postcode"]}] {entry["name"]}; {entry["address"]} [{entry["city"]}]>[{entry["telephone"]}]')

        cache.write(new_entry)


    ne_1, ne_2, sw_1, sw_2 = bounding_box(map_points)
    x = skipper_record(ne_2, ne_1, sw_2, sw_1, cache.getbuffer().nbytes)
    unpacked_data = struct.unpack('<Bi4i', x)
    print(cache.getbuffer().nbytes)

    print(f"{unpacked_data[0]} {unpacked_data[1]} {unpacked_data[2] / 100000} {unpacked_data[3] / 100000} {unpacked_data[4] / 100000} {unpacked_data[5] / 100000}")

    with open("stations.ov2", "wb+") as f:
        f.write(x)
        f.write(cache.getvalue())
