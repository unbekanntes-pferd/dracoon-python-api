"""
Export Room Log DRACOON Server with CLI Params
21.02.2021 Quirin Wierer
"""

from operator import concat
from pickle import TRUE
from dracoon import DRACOON
import asyncio
import csv
import argparse
import sys

# parse CLI arguments
def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("-r", "--roompath", required=True, help="Path to Dataroom in quotationmarks. Take care of potential spaces!")
    ap.add_argument("-s", "--startdate", required=True, help="Included start date for roomlog in YYYY-MM-DD format.")
    ap.add_argument("-e", "--enddate", required=True, help="Included end date for roomlog in YYYY-MM-DD format.")
    args = vars(ap.parse_args())

    # if no roompath/startdate/enddate is given, exit
    if args["roompath"] is None:
        print("Providing a roompath is mandatory.")
        sys.exit(2)
    else:
        room_path = args["roompath"]

    if args["startdate"] is None:
        print("Providing a startdate is mandatory.")
        sys.exit(2)
    else:
        start_date = args["startdate"]

    if args["enddate"] is None:
        print("Providing a enddate is mandatory.")
        sys.exit(2)
    else:
        end_date = args["enddate"]
    
    return room_path, start_date, end_date 

 
async def main():
    baseURL = 'https://dracoon.server'
    client_id = 'XXXXXXXXXXX'
    client_secret = 'XXXXXXXXXX'

    #parse CLI arguments
    room_path, start_date, end_date = parse_arguments()
    timestamp_start = start_date+'T00:00:00'
    timestamp_end = end_date+'T23:59:59'

    #authenticate
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)

    #retrieve roomID
    node_info = await dracoon.nodes.get_node_from_path(room_path)
    ROOM_ID = node_info.id

    fileName = 'Report of Dataroom '+room_path[1:]+' '+start_date+' - '+end_date+'.csv'
    
    # retrieve roomlogs
    roomevents = await dracoon.nodes.get_room_events(room_id=ROOM_ID, date_start=timestamp_start, date_end=timestamp_end, raise_on_err=True)
    event_list = [*roomevents.items]
    if roomevents.range.total > 500:
        for offset in range(500,roomevents.range.total,500):
            event_list = await dracoon.nodes.get_room_events(room_id=ROOM_ID, date_start=timestamp_start, date_end=timestamp_end, raise_on_err=True,offset=offset)
            event_list = [*roomevents.items]

    # create CSV in current directory, write header, iterate through results
    with open(fileName, 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow(['id', 'time', 'status', 'operationName', 'message'])

        for LogEvent in event_list:
            if LogEvent.status == 0:
                operation_status = 'Success'
            elif LogEvent.status == 2:
                operation_status = 'Error'

            csv_writer.writerow([LogEvent.id, LogEvent.time, operation_status, LogEvent.operationName, LogEvent.message])

    print(f'CSV room report (room id: {ROOM_ID}) created: ' + fileName)

    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())