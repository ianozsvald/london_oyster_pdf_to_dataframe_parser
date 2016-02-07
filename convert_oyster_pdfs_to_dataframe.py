import re
import glob
import os
import argparse
import datetime
import unittest
import textract
from dateutil import parser as dt_parser
import pandas as pd

lines_to_ignore = ["* Adjustments to past fares",
                   "Some journeys were cheaper or free today",
                   "We have no record of where you touched",
                   "Page",
                   "cap.",
                   "We have auto completed"]

def plain_text_message(line):
    for ignore in lines_to_ignore:
        if line.startswith(ignore):
            return True
    return False


def convert_price(line):
    """Convert line to price (float) or raise ValueError"""
    # line might be '£2.90' or something else
    matches = re.findall("(\d+\.\d+)", line)
    if not matches:
        raise ValueError()
    price = float(matches[0])
    assert price >= 0, "We expect positive prices over £0.0"
    assert price < 100, "We don't expect a charge over £100"
    return price


def date_like(line):
    """Check if we have 2 slashes and numbers"""
    # line might be "28/01/2016"
    if line.count("/") == 2:
        line_no_slashes = line.replace("/", "")
        try:
            int(line_no_slashes)
        except ValueError:
            return False
        return True
    return False

def time_like(line):
    """Test if a line looks like a timestamp"""
    # line might be like '12:33 - 12:48' or '19:03'
    if line.count(':') == 2:
        if line.count('-') >= 1:
            line_without = line.replace(':', '')
            line_without = line_without.replace('-', '')
            line_without = line_without.replace(' ', '')
            try:
                int(line_without)
                return True
            except ValueError:
                pass

    if line.count(':') == 1:
        line_without = line.replace(':', '')
        try:
            int(line_without)
            return True
        except ValueError:
            pass
    return False


def blocks_look_sane(block):
    # 1st item might be 'price' or 'text', if
    # it is 'price' then the PDF was correctly parsed
    # but if 'text' then it needs fixing
    looks_good = True
    if block[1][0] != 'price':
        looks_good = False
    # each block should end with 'time'
    if block[-1][0] != 'time':
        looks_good = False

    return looks_good


def fix_blocks(block):
    if block[1][0] != "price":
        price = block[2]
        txt = block[1]
        # swap orders of these badly parsed items
        block[1] = price
        block[2] = txt

    if block[-1][0] == 'price':
        # sometimes a price is added as an adjustment, we can ignore this
        block = block[:-1]
    assert blocks_look_sane(block)
    return block



class Tests(unittest.TestCase):
    def test_time_like(self):
        good_times = ['12:33 - 12:48', '--:-- - 23:47', '18:24']
        for good_time in good_times:
            assert time_like(good_time)
        bad_times = ['06/01/2016', 'Stuff']
        for bad_time in bad_times:
            assert not time_like(bad_time)

    def test_date_like(self):
        good_dates = ['06/01/2016', '14/01/2016', '01/01/2015']
        for good_date in good_dates:
            assert date_like(good_date)


    def test_block_in_right_order(self):
        """Check we've fixed the mis-ordered price/date at the start of the list"""
        good_list = [('date', datetime.date(2016, 1, 9)), ('price', 9.3), ('text', 'Kentish Town'), ('text', 'Bank'), ('price', 2.4), ('time', '10:01 - 10:25'), ('text', 'Monument'), ('text', 'Kent House'), ('price', 4.3), ('time', '12:17 - 13:17'), ('text', 'Sydenham SR'), ('text', 'Kentish Town'), ('price', 2.6), ('time', '18:19 - 19:08')]
        assert blocks_look_sane(good_list)
        bad_list = [('date', datetime.date(2016, 1, 8)), ('text', 'Kentish Town'), ('price', 5.8), ('text', 'Leicester Square'), ('price', 2.9), ('time', '08:46 - 09:01'), ('text', 'Leicester Square'), ('text', 'Kentish Town'), ('price', 2.9), ('time', '18:33 - 18:52')]
        assert not blocks_look_sane(bad_list)
        fix_blocks(bad_list)

    #def test_journeys(self):
        #bus = [('date', datetime.date(2016, 1, 30)), ('price', 1.5), ('text', 'Bus Journey, Route 46'), ('price', 1.5), ('time', '14:49')]
        #tube_tube_tube = [('date', datetime.date(2016, 1, 28)), ('price', 6.5), ('text', 'Kentish Town'), ('text', 'Leicester Square'), ('price', 2.9), ('time', '08:59 - 09:15'), ('text', 'Leicester Square'), ('text', 'Old Street'), ('price', 2.4), ('time', '18:00 - 18:19'), ('text', 'Old Street'), ('text', 'Kentish Town'), ('price', 1.2), ('time', '22:43 - 23:01')]
        #tube_tube_bus = [('date', datetime.date(2016, 1, 10)), ('price', 6.3), ('text', 'Kentish Town'), ('text', 'Old Street'), ('price', 2.4), ('time', '17:39 - 17:55'), ('text', 'Old Street'), ('text', 'Camden Town'), ('price', 2.4), ('time', '22:10 - 22:27'), ('text', 'Bus Journey, Route C2'), ('price', 1.5), ('time', '22:28')]


def add_item(typ, value, block_of_lines):
    block_of_lines.append((typ, value))


def process_block(block_of_lines):
    parsed_items = []
    if len(block_of_lines):
        block_of_lines = fix_blocks(block_of_lines)
        #print(block_of_lines)
        block_date = block_of_lines[0]
        assert block_date[0] == 'date'
        date = block_date[1]
        idx = 2  # start by jumping the first price (this is the day's price)
        while True:
            if idx == len(block_of_lines):
                break
            assert block_of_lines[idx][0] == "text", "We've not advanced correctly?! {} '{}'".format(idx, repr(block_of_lines))
            is_train = block_of_lines[idx][0] == 'text' and block_of_lines[idx+1][0] == 'text'
            frm = block_of_lines[idx][1]
            # tubes specify destination, bus doesn't
            if is_train:
                to = block_of_lines[idx+1][1]
            else:
                to = ""
            # we could optionally add the time in here
            parsed_items.append({'date': date,
                                 'from': frm,
                                 'to': to,
                                 'is_train': is_train})

            jump_by = 3 # text, price, time
            if is_train:
                jump_by += 1
            idx += jump_by

    return parsed_items


def process_pdf_txt(txt):
    processed_blocks = []
    block_of_lines = []
    in_dt_block = False
    found_first_dateblock = False

    for line in txt.split("\n"):
        line = line.strip()
        if line:
            if not plain_text_message(line):

                if date_like(line):
                    try:
                        dt = dt_parser.parse(line, dayfirst=True)
                        date = dt.date() # just extract the date, ignore the 00:00 time

                        # we have a new date so show the last set of lines
                        processed_blocks += process_block(block_of_lines)

                        block_of_lines = []
                        add_item("date", date, block_of_lines)
                        in_dt_block = True
                        found_first_dateblock = True
                        continue
                    except ValueError:
                        pass

                try:
                    price = convert_price(line)
                    add_item('price', price, block_of_lines)
                    continue
                except ValueError:
                    pass

                if time_like(line):
                    add_item('time', line, block_of_lines)
                    continue

                if in_dt_block:
                    add_item('text', line, block_of_lines)
                    continue

                if found_first_dateblock:
                    assert False, "We shouldn't be here!"

    if len(block_of_lines):
        processed_blocks += process_block(block_of_lines)
    return processed_blocks


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Project description for this prototype...',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # These two lines show a positional (mandatory) argument and an optional argument
    # parser.add_argument('positional_arg', type=str, help='required positional argument')
    parser.add_argument('--filename', default=None, help="PDF filename to parse")
    parser.add_argument('--directory', default=None, help="Directory to glob for PDF files")
    parser.add_argument("--output_filename", default="journeys.hdf5", help="HDF5 data for our journeys")
    args = parser.parse_args()

    if args.filename:
        filenames = [args.filename]
    if args.directory:
        filenames = glob.glob(os.path.join(args.directory, '*.pdf'))

    all_processed_blocks = []
    for filename in filenames:
        print("Processing", filename)
        raw = textract.process(filename, method="pdftotext")
        txt = raw.decode('utf-8')
        processed_blocks = process_pdf_txt(txt)
        all_processed_blocks += processed_blocks

    # build dataframe, set date as the index, output as an HDF5 file
    df = pd.DataFrame(all_processed_blocks)
    df = df.set_index('date').sort(ascending=False)
    print("Writing {} rows to {}".format(df.shape, args.output_filename))
    df.to_hdf(args.output_filename, key="journeys")
