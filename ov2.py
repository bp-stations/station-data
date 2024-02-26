import argparse
import io
import json
import logging
import struct
from enum import Enum
from io import BytesIO


logging.basicConfig(level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)
data = []


class Record:
    class Type(Enum):
        deleted = 0
        skipper = 1
        regular = 2
        extended = 3


def to_ov2(lon, lat, label):
    lon = int(lon * 100000)
    lat = int(lat * 100000)
    label = label.encode('raw_unicode_escape')
    size = 14 + len(label)
    buff = struct.pack(f'<B3i{len(label) + 1}s', 2, size, lon, lat, label)
    return buff


def from_ov2_simple(buff):
    status, size, lon, lat, label = struct.unpack(f'<B3i{len(buff) - 14}sx', buff)
    lon /= 100000
    lat /= 100000
    label = label.decode('raw_unicode_escape')
    logging.info(f"decoded simple record: {status} {size} {lon} {lat} {label}")


def from_ov2_skipper(buff):
    _type, size, ne_long_2, ne_lat_2, sw_long_2, sw_lat_2 = struct.unpack(f'<Bi4i', buff)
    logging.info(f"decoded skipper record: {_type} {size} {ne_long_2} {ne_lat_2} {sw_long_2} {sw_lat_2}")


def skipper_record(ne_long, ne_lat, sw_long, sw_lat, skip=0):
    size = 21 + skip
    ne_long_2 = int(ne_long * 100000)
    ne_lat_2 = int(ne_lat * 100000)
    sw_long_2 = int(sw_long * 100000)
    sw_lat_2 = int(sw_lat * 100000)
    buff = struct.pack(f'<Bi4i', Record.Type.skipper.value, size, ne_long_2, ne_lat_2, sw_long_2, sw_lat_2)
    return buff


def bounding_box(points):
    # we get point (latitude, longitude)
    x_coordinates, y_coordinates = zip(*points)
    # x_coordinates = latitude
    # y_coordinates = longitude

    return max(x_coordinates), max(y_coordinates), min(x_coordinates), min(y_coordinates)


# x1 and y1 define northeast
# x2 and y2 define southwest
def check_data(x1, y1, x2, y2, local_json, last_split=0):
    """
    We get 4 cords and a split value. With that we check if more than 20 points are inside
    If there are more than 20 then we split the coordinates in half first from East/West and then North/South
    After that the direction gets swapped every time
    :param x1: lat / North
    :param y1: long / East
    :param x2: lat / south
    :param y2: long / West
    :param local_json: json
    :param last_split:
    :return:
    """
    if x1 > x2:
        x2, x1 = x1, x2

    if y1 > y2:
        y2, y1 = y1, y2

    a = 0
    b = 0
    local_data = []
    for local_station_entry in local_json:
        # print(f"{x1} {entry["lat"]} {x2}")
        # print(f"{y1} {entry["lng"]} {y2}")
        if x1 <= local_station_entry["lat"] <= x2 and y1 <= local_station_entry["lng"] <= y2:
            # print("point inside")
            local_data.append(local_station_entry)
            a +=1
        else:
            # print("point outside")
            b += 1

    if a > 20:
        logging.info(f"too many points for {x1} {x2} {y1} {y2} inside. splitting")
        if last_split != 0:
            if last_split == 1:
                last_split = 2
            elif last_split == 2:
                last_split = 1
        else:
            last_split = 1

        if last_split == 1:
            midpoint = (y1 + y2) / 2
            check_data(x1, midpoint, x2, y2, local_json, 1)
            check_data(x1, y1, x2, midpoint, local_json, 1)
        elif last_split == 2:
            midpoint = (x1 + x2) / 2
            check_data(midpoint, y1, x2, y2, local_json, 2)
            check_data(x1, y1, midpoint, y2, local_json, 2)

    else:
        if a > 0:
            logging.info(f"good data for {x1} {x2} {y1} {y2} with {a} stations")
            data.append(local_data)


def generate_ov2(tmp_args):
    json_data = json.load(tmp_args.input)

    # get all lat / long cords
    map_points = []
    for entry in json_data:
        map_points.append((entry["lat"], entry["lng"]))

    # generate a box around all map points
    ne_1, ne_2, sw_1, sw_2 = bounding_box(map_points)
    z_1, z_2, v_1, v_2 = ne_1, ne_2, sw_1, sw_2
    logging.info(f"bounding box of all items ne_1: {ne_1}, ne_2: {ne_2}, sw_1: {sw_1}, sw_2: {sw_2}")

    # start box generation
    check_data(ne_1, ne_2, sw_1, sw_2, json_data, 0)

    logging.info(f"i have {len(data)} zones")
    logging.info(f"originally got {len(json_data)} stations")
    x = 0
    for map_point_list in data:
        x += len(map_point_list)
    logging.info(f"now got {x} stations")

    all_data = BytesIO()

    for map_point_list in data:
        map_points = []
        cache = BytesIO()
        if len(map_point_list) == 0:
            continue

        for point in map_point_list:
            map_points.append((point["lat"], point["lng"]))
            new_entry = to_ov2(point["lng"], point["lat"],
                               f'[{point["country_code"]}-{point["postcode"]}] {point["name"]}; {point["address"]} '
                               f'[{point["city"]}]>[{point["telephone"]}]')
            cache.write(new_entry)

        tmp_ne_1, tmp_ne_2, tmp_sw_1, tmp_sw_2 = bounding_box(map_points)
        tmp_skipper = skipper_record(tmp_ne_2, tmp_ne_1, tmp_sw_2, tmp_sw_1, cache.getbuffer().nbytes)
        all_data.write(tmp_skipper)
        all_data.write(cache.getbuffer())

    # now lets wrap a skipper record around all points in the file
    # e.g. if you have a map that only has points in europe and you are currently in africa then skip the whole file
    logging.info(f"bounding box of all items z_1: {z_1}, z_2: {z_2}, v_1: {v_1}, v_2: {v_2}")
    skipper_all = skipper_record(z_2, z_1, v_2, v_1, all_data.getbuffer().nbytes)
    tmp_args.output.write(skipper_all)
    tmp_args.output.write(all_data.getvalue())


def get_type(buffer):
    _type = struct.unpack("<B", buffer)[0]
    return _type


def decode_record(local_file, location):
    local_file.seek(location, 0)
    x = local_file.read(1)
    return get_type(x)


def get_file_size(tmp_file: io.BufferedReader):
    tmp_cache = BytesIO()
    tmp_cache.write(tmp_file.read())
    return tmp_cache.getbuffer().nbytes


def decode(tmp_args):
    tmp_data: io.BufferedReader = tmp_args.input
    current_cursor = 0
    tmp_file_byte_size = get_file_size(tmp_data)
    while True:
        if current_cursor == tmp_file_byte_size:
            logging.info("reached end of file")
            break
        tmp_record = decode_record(tmp_data, current_cursor)

        if tmp_record == 1:
            tmp_data.seek(current_cursor, 0)
            from_ov2_skipper(tmp_data.read(21))
            current_cursor += 21
        elif tmp_record == 2:
            tmp_data.seek(current_cursor, 0)
            _type, local_size = struct.unpack("<Bi", tmp_data.read(5))
            tmp_data.seek(current_cursor, 0)
            from_ov2_simple(tmp_data.read(local_size))
            current_cursor += local_size
        else:
            logging.warning(f"got unknown type at {current_cursor} {tmp_record}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a json file to ov2 with skipper records")
    subparsers = parser.add_subparsers(title='subcommands', help='additional help', required=True)

    x = subparsers.add_parser('generate')
    x.add_argument("-i", "--input", help="input file", required=True,
                            type=argparse.FileType('r', encoding="utf-8"))
    x.add_argument("-o", "--output", help="output file", required=True, type=argparse.FileType('wb+'))
    x.set_defaults(func=generate_ov2)

    y = subparsers.add_parser('decode')
    y.add_argument("-i", "--input", help="input file", required=True,
                   type=argparse.FileType('rb'))
    y.set_defaults(func=decode)

    args = parser.parse_args()
    args.func(args)
