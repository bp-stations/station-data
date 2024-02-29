#!/usr/bin/env python3
import os
import io
import json
import struct
import logging
import argparse
from pathlib import Path

import simplekml
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


def to_ov2(x, y, label):
    """
    :param x: longitude coordinate of the POI
    :param y: latitude coordinate of the POI
    :param label: zero-terminated ASCII string specifying the name of the POI
    :return:
    """
    x = int(x * 100000)
    y = int(y * 100000)
    label = label.encode('raw_unicode_escape')
    size = 14 + len(label)
    buff = struct.pack(f'<B3i{len(label) + 1}s', 2, size, x, y, label)
    return buff


def from_ov2_simple(buff):
    status, size, lon, lat, label = struct.unpack(f'<B3i{len(buff) - 14}sx', buff)
    lon /= 100000
    lat /= 100000
    label = label.decode('raw_unicode_escape')
    logging.info(f"decoded simple record: {status} {size} {lat} {lon} {label}")
    return status, size, lon, lat, label


def from_ov2_skipper(buff):
    _type, size, tmp_west, tmp_south, tmp_east, tmp_north = struct.unpack(f'<Bi4i', buff)
    tmp_west /= 100000
    tmp_south /= 100000
    tmp_east /= 100000
    tmp_north /= 100000
    logging.info(f"decoded skipper record: {_type} {size} {tmp_west} {tmp_south} {tmp_east} {tmp_north}")
    return _type, size, tmp_west, tmp_south, tmp_east, tmp_north


def skipper_record(x1, y1, x2, y2, skip=0):
    """
    :param x1: longitude coordinate of the west edge of the rectangle
    :param y1: latitude coordinate of the south edge of the rectangle
    :param x2: longitude coordinate of the east edge of the rectangle
    :param y2: latitude coordinate of the north edge of the rectangle
    :param skip: the size to skip, excluding the skipper record
    :return:
    """
    size = 21 + skip

    # check if x1 is west and if not swap them
    if x1 > x2:
        x2, x1 = x1, x2

    # check if y1 is south and if not swap them
    if y1 > y2:
        y2, y1 = y1, y2

    x1 = int(x1 * 100000)
    y1 = int(y1 * 100000)
    x2 = int(x2 * 100000)
    y2 = int(y2 * 100000)

    buff = struct.pack(f'<Bi4i', Record.Type.skipper.value, size, x1, y1, x2, y2)
    return buff


def bounding_box(points) -> [float, float, float, float]:
    """
    :param points:
    :return:
    x1 = west
    y1 = south
    x2 = east
    y2 = north
    """
    # we get point (long, lat)
    # x = long, y = lat
    x_coordinates, y_coordinates = zip(*points)
    # x_coordinates = latitude
    # y_coordinates = longitude

    return min(x_coordinates), min(y_coordinates), max(x_coordinates), max(y_coordinates),


# x1 and y1 define northeast
# x2 and y2 define southwest
def check_data(x1, y1, x2, y2, local_json, new_split=2):
    """
    We get 4 cords and a split value. With that we check if more than 20 points are inside
    If there are more than 20 then we split the coordinates in half first from East/West and then North/South
    After that the direction gets swapped every time
    :param x1: long of east or west
    :param y1: lat of north or south
    :param x2: long of east or west
    :param y2: lat of north or south
    :param local_json: json
    :param new_split:
    :return:
    """

    # check if x1 is west and if not swap them
    if x1 > x2:
        x2, x1 = x1, x2

    # check if y1 is south and if not swap them
    if y1 > y2:
        y2, y1 = y1, y2

    a = 0
    b = 0
    local_data = []
    for local_station_entry in local_json:
        if x1 <= local_station_entry["lat"] <= x2 and y1 <= local_station_entry["lng"] <= y2:
            local_data.append(local_station_entry)
            a += 1
        else:
            b += 1

    if a > 20:
        logging.info(f"too many points for {x1} {y1} {x2} {y2} inside. splitting")
        if new_split == 1:
            # split east / west
            new_split = 2
        else:
            # split north / south
            new_split = 1

        if new_split == 1:
            # split north / south
            midpoint = (y1 + y2) / 2
            check_data(x1, midpoint, x2, y2, local_json, 1)
            check_data(x1, y1, x2, midpoint, local_json, 1)
        elif new_split == 2:
            # split east / west
            midpoint = (x1 + x2) / 2
            check_data(midpoint, y1, x2, y2, local_json, 2)
            check_data(x1, y1, midpoint, y2, local_json, 2)

    else:
        if a > 0:
            logging.info(f"good data for {x1} {y1} {x2} {y2} with {a} stations")
            data.append(local_data)


def generate_ov2(tmp_args):
    json_data = json.load(tmp_args.input)

    # get all lat / long cords
    map_points = []
    for entry in json_data:
        map_points.append((entry["lng"], entry["lat"]))

    # generate a box around all map points
    west, south, east, north = bounding_box(map_points)
    west2, south2, east2, north2 = west, south, east, north
    logging.info(f"bounding box of all items ne_1: {west}, ne_2: {south}, sw_1: {east}, sw_2: {north}")

    # start box generation
    check_data(west, south, east, north, json_data, 0)

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
            map_points.append((point["lng"], point["lat"]))
            new_entry = to_ov2(point["lng"], point["lat"],
                               f'[{point["country_code"]}-{point["postcode"]}] {point["name"]}; {point["address"]} '
                               f'[{point["city"]}]>[{point["telephone"]}]')
            cache.write(new_entry)

        tmp_west, tmp_south, tmp_east, tmp_north = bounding_box(map_points)
        tmp_skipper = skipper_record(tmp_west, tmp_south, tmp_east, tmp_north, cache.getbuffer().nbytes)
        all_data.write(tmp_skipper)
        all_data.write(cache.getbuffer())

    # now lets wrap a skipper record around all points in the file
    # e.g. if you have a map that only has points in europe, and you are currently in africa then skip the whole file
    logging.info(f"bounding box of all items west: {west2}, south: {south2}, east: {east2}, north: {north2}")
    skipper_all = skipper_record(west2, south2, east2, north2, all_data.getbuffer().nbytes)
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


def convert(tmp_args):
    tmp_kml = simplekml.Kml()
    tmp_data: io.BufferedReader = tmp_args.input
    current_cursor = 0
    current_items = 0
    tmp_file_byte_size = get_file_size(tmp_data)
    tmp_folder = tmp_kml.newfolder(name="0")
    while True:
        if current_cursor == tmp_file_byte_size:
            logging.info("reached end of file")
            break
        tmp_record = decode_record(tmp_data, current_cursor)

        if tmp_record == 1:
            tmp_data.seek(current_cursor, 0)
            _type, size, tmp_west, tmp_south, tmp_east, tmp_north = from_ov2_skipper(tmp_data.read(21))
            tmp_folder.newpolygon(outerboundaryis=[(tmp_south, tmp_west), (tmp_north, tmp_west),
                                                   (tmp_south, tmp_east), (tmp_north, tmp_east)],
                                  innerboundaryis=[(tmp_south, tmp_west), (tmp_north, tmp_west),
                                                   (tmp_south, tmp_east), (tmp_north, tmp_east)])
            current_items += 1
            current_cursor += 21
        elif tmp_record == 2:
            tmp_data.seek(current_cursor, 0)
            _type, local_size = struct.unpack("<Bi", tmp_data.read(5))
            tmp_data.seek(current_cursor, 0)
            status, size, tmp_lng, tmp_lat, tmp_name = from_ov2_simple(tmp_data.read(local_size))
            tmp_folder.newpoint(name=tmp_name, coords=[(tmp_lng, tmp_lat)])
            current_items += 1
            current_cursor += local_size
        else:
            logging.warning(f"got unknown type at {current_cursor} {tmp_record}")

        if current_items >= 1999:
            tmp_kml.save("output.kml", format=False)
            exit()


def auto(tmp_args):
    input_path = Path(__file__).parent.absolute().joinpath('./out/json/')
    output_path = Path(__file__).parent.absolute().joinpath('./out/ov2/')
    folders = ["all", "brands", "countries"]
    logging.info("automatically converting all files in out/json to ov2")
    for folder_name in folders:
        tmp_path_input = input_path.joinpath(folder_name)
        tmp_path_output = output_path.joinpath(folder_name)
        try:
            os.mkdir(tmp_path_output)
        except FileExistsError:
            pass

        for tmp_file in os.listdir(tmp_path_input):
            if tmp_file.startswith("."):
                continue
            if "_min.json" in tmp_file:
                continue
            logging.info(f"converting {tmp_path_input.joinpath(tmp_file)} to "
                         f"{tmp_path_output.joinpath(tmp_file.replace(".json", ".ov2"))}")
            tmp_args = parser.parse_args(['generate', '-i', str(tmp_path_input.joinpath(tmp_file)), '-o',
                                          str(tmp_path_output.joinpath(tmp_file.replace(".json", ".ov2")))])
            generate_ov2(tmp_args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a json file to ov2 with skipper records")
    subparsers = parser.add_subparsers(title='subcommands', help='additional help', required=True)

    tmp_parser_generate = subparsers.add_parser('generate')
    tmp_parser_generate.add_argument("-i", "--input", help="input file", required=True,
                                     type=argparse.FileType('r', encoding="utf-8"))
    tmp_parser_generate.add_argument("-o", "--output", help="output file", required=True, type=argparse.FileType('wb+'))
    tmp_parser_generate.set_defaults(func=generate_ov2)

    tmp_parser_decode = subparsers.add_parser('decode')
    tmp_parser_decode.add_argument("-i", "--input", help="input file", required=True,
                                   type=argparse.FileType('rb'))
    tmp_parser_decode.set_defaults(func=decode)

    tmp_parser_convert = subparsers.add_parser('convert')
    tmp_parser_convert.add_argument("-i", "--input", help="input file", required=True,
                                    type=argparse.FileType('rb'))
    tmp_parser_convert.set_defaults(func=convert)

    tmp_parser_auto = subparsers.add_parser('auto')
    tmp_parser_auto.set_defaults(func=auto)

    args = parser.parse_args()
    args.func(args)
